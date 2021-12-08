import configparser
import datetime
import errno
import json
import logging
import math
import os.path
import pyperf
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import pyperformance
from pyperformance._utils import MS_WINDOWS
from pyperformance.venv import (GET_PIP_URL, REQ_OLD_PIP, PERFORMANCE_ROOT,
                                download, is_build_dir)


GIT = True
DEFAULT_BRANCH = 'master' if GIT else 'default'
LOG_FORMAT = '%(asctime)-15s: %(message)s'

EXIT_ALREADY_EXIST = 10
EXIT_COMPILE_ERROR = 11
EXIT_VENV_ERROR = 11
EXIT_BENCH_ERROR = 12


def parse_date(text):
    def replace_timezone(regs):
        text = regs.group(0)
        return text[:2] + text[3:]

    # replace '+01:00' with '+0100'
    text2 = re.sub(r'[0-9]{2}:[0-9]{2}$', replace_timezone, text)

    # ISO 8601 with timezone: '2017-03-30T19:12:18+00:00'
    return datetime.datetime.strptime(text2, "%Y-%m-%dT%H:%M:%S%z")


class Task(object):
    def __init__(self, app, cwd):
        self.app = app
        self.cwd = cwd

    def get_output_nocheck(self, *cmd):
        return self.app.get_output_nocheck(*cmd, cwd=self.cwd)

    def get_output(self, *cmd):
        return self.app.get_output(*cmd, cwd=self.cwd)

    def run_nocheck(self, *cmd, **kw):
        return self.app.run_nocheck(*cmd, cwd=self.cwd, **kw)

    def run(self, *cmd, **kw):
        self.app.run(*cmd, cwd=self.cwd, **kw)


class Repository(Task):
    def __init__(self, app, path):
        super().__init__(app, path)
        self.logger = app.logger
        self.app = app
        self.conf = app.conf

    def fetch(self):
        if GIT:
            self.run('git', 'fetch')
        else:
            self.run('hg', 'pull')

    def parse_revision(self, revision):
        branch_rev = '%s/%s' % (self.conf.git_remote, revision)

        exitcode, stdout = self.get_output_nocheck('git', 'rev-parse',
                                                   '--verify', branch_rev)
        if not exitcode:
            return (True, branch_rev, stdout)

        exitcode, stdout = self.get_output_nocheck('git', 'rev-parse',
                                                   '--verify', revision)
        if not exitcode and stdout.startswith(revision):
            revision = stdout
            return (False, revision, revision)

        self.logger.error("ERROR: unable to parse revision %r" % (revision,))
        sys.exit(1)

    def checkout(self, revision):
        if GIT:
            # remove all untracked files
            self.run('git', 'clean', '-fdx')

            # checkout to requested revision
            self.run('git', 'reset', '--hard', 'HEAD')
            self.run('git', 'checkout', revision)

            # remove all untracked files
            self.run('git', 'clean', '-fdx')
        else:
            self.run('hg', 'up', '--clean', '-r', revision)
            # FIXME: run hg purge?

    def get_revision_info(self, revision):
        if GIT:
            cmd = ['git', 'show', '-s', '--pretty=format:%H|%ci', '%s^!' % revision]
        else:
            cmd = ['hg', 'log', '--template', '{node}|{date|isodate}', '-r', revision]
        stdout = self.get_output(*cmd)
        if GIT:
            node, date = stdout.split('|')
            date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S %z')
            # convert local date to UTC
            date = (date - date.utcoffset()).replace(tzinfo=datetime.timezone.utc)
        else:
            node, date = stdout.split('|')
            date = datetime.datetime.strptime(date[:16], '%Y-%m-%d %H:%M')
        return (node, date)


class Application(object):
    def __init__(self, conf, options):
        self.conf = conf
        self.options = options
        logging.basicConfig(format=LOG_FORMAT)
        self.logger = logging.getLogger()
        self.log_filename = None

    def setup_log(self, prefix):
        prefix = re.sub('[^A-Za-z0-9_-]+', '_', prefix)
        prefix = re.sub('_+', '_', prefix)

        date = datetime.datetime.now()
        date = date.strftime('%Y-%m-%d_%H-%M-%S.log')
        filename = '%s-%s' % (prefix, date)
        self.log_filename = os.path.join(self.conf.directory, filename)

        log = self.log_filename
        if os.path.exists(log):
            self.logger.error("ERROR: Log file %s already exists" % log)
            sys.exit(1)
        self.safe_makedirs(os.path.dirname(log))

        handler = logging.FileHandler(log)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def create_subprocess(self, cmd, **kwargs):
        self.logger.error("+ %s" % ' '.join(map(shlex.quote, cmd)))
        return subprocess.Popen(cmd, **kwargs)

    def run_nocheck(self, *cmd, stdin_filename=None, **kwargs):
        if stdin_filename:
            stdin_file = open(stdin_filename, "rb", 0)
            kwargs['stdin'] = stdin_file.fileno()
        else:
            stdin_file = None
        log_stdout = kwargs.pop('log_stdout', True)

        if log_stdout:
            kwargs['stdout'] = subprocess.PIPE
            kwargs['stderr'] = subprocess.STDOUT
            kwargs['universal_newlines'] = True

        try:
            proc = self.create_subprocess(cmd, **kwargs)

            # FIXME: support Python 2?
            with proc:
                if log_stdout:
                    for line in proc.stdout:
                        line = line.rstrip()
                        self.logger.error(line)
                exitcode = proc.wait()
        finally:
            if stdin_file is not None:
                stdin_file.close()

        if exitcode:
            cmd_str = ' '.join(map(shlex.quote, cmd))
            self.logger.error("Command %s failed with exit code %s"
                              % (cmd_str, exitcode))

        return exitcode

    def run(self, *cmd, **kw):
        exitcode = self.run_nocheck(*cmd, **kw)
        if exitcode:
            sys.exit(exitcode)

    def get_output_nocheck(self, *cmd, **kwargs):
        proc = self.create_subprocess(cmd,
                                      stdout=subprocess.PIPE,
                                      universal_newlines=True,
                                      **kwargs)
        # FIXME: support Python 2?
        with proc:
            stdout = proc.communicate()[0]

        stdout = stdout.rstrip()

        exitcode = proc.wait()
        if exitcode:
            cmd_str = ' '.join(map(shlex.quote, cmd))
            self.logger.error("Command %s failed with exit code %s"
                              % (cmd_str, exitcode))

        return (exitcode, stdout)

    def get_output(self, *cmd, **kwargs):
        exitcode, stdout = self.get_output_nocheck(*cmd, **kwargs)
        if exitcode:
            for line in stdout.splitlines():
                self.logger.error(line)
            sys.exit(exitcode)

        return stdout

    def safe_rmdir(self, directory):
        if os.path.exists(directory):
            self.logger.error("Remove directory %s" % directory)
            shutil.rmtree(directory)

    def safe_makedirs(self, directory):
        try:
            os.makedirs(directory)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise


def resolve_python(prefix, builddir, *, fallback=True):
    if sys.platform in ('darwin', 'win32'):
        program_ext = '.exe'
    else:
        program_ext = ''

    if prefix:
        if sys.platform == 'darwin':
            program_ext = ''
        program = os.path.join(prefix, "bin", "python3" + program_ext)
        exists = os.path.exists(program)
        if not exists and fallback:
            program2 = os.path.join(prefix, "bin", "python" + program_ext)
            if os.path.exists(program2):
                program = program2
                exists = True
    else:
        assert builddir
        program = os.path.join(builddir, "python" + program_ext)
        exists = os.path.exists(program)
    return program, exists


class Python(Task):
    def __init__(self, app, conf):
        super().__init__(app, conf.build_dir)
        self.app = app
        self.branch = app.branch
        self.conf = conf
        self.logger = app.logger
        self.program = None
        self.hexversion = None

    def patch(self, filename):
        if not filename:
            return

        self.logger.error('Apply patch %s in %s (revision %s)'
                          % (filename, self.conf.repo_dir, self.app.revision))
        self.app.run('patch', '-p1',
                     cwd=self.conf.repo_dir,
                     stdin_filename=filename)

    def compile(self):
        build_dir = self.conf.build_dir

        self.app.safe_rmdir(build_dir)
        self.app.safe_makedirs(build_dir)

        config_args = []
        if self.branch.startswith("2.") and not MS_WINDOWS:
            # On Python 2, use UCS-4 for Unicode on all platforms, except
            # on Windows which uses UTF-16 because of its 16-bit wchar_t
            config_args.append('--enable-unicode=ucs4')
        if self.conf.prefix:
            config_args.extend(('--prefix', self.conf.prefix))
        if self.conf.debug:
            config_args.append('--with-pydebug')
        elif self.conf.lto:
            config_args.append('--with-lto')
        if self.conf.pkg_only:
            config_args.extend(self.get_package_only_flags())
        if self.conf.debug:
            config_args.append('CFLAGS=-O0')
        configure = os.path.join(self.conf.repo_dir, 'configure')
        self.run(configure, *config_args)

        if self.conf.pgo:
            # FIXME: use taskset (isolated CPUs) for PGO?
            self.run('make', 'profile-opt')
        else:
            self.run('make')

    def install_python(self):
        program, _ = resolve_python(
            self.conf.prefix if self.conf.install else None,
            self.conf.build_dir,
        )
        if self.conf.install:
            program, _ = resolve_python(self.conf.prefix, self.conf.build_dir)
            self.app.safe_rmdir(self.conf.prefix)
            self.app.safe_makedirs(self.conf.prefix)
            self.run('make', 'install')
        else:
            program, _ = resolve_python(None, self.conf.build_dir)
        # else don't install: run python from the compilation directory
        self.program = program

    def get_version(self):
        # Dump the Python version
        self.logger.error("Installed Python version:")
        self.run(self.program, '--version')

        # Get the Python version
        code = 'import sys; print(sys.hexversion)'
        stdout = self.get_output(self.program, '-c', code)
        self.hexversion = int(stdout)
        self.logger.error("Python hexversion: %x" % self.hexversion)

    def get_package_only_flags(self):
        arguments = []
        extra_paths = []

        for pkg in self.conf.pkg_only:
            prefix = self.get_package_prefix(pkg)
            if pkg == 'openssl':
                arguments.append('--with-openssl=' + prefix)
            else:
                extra_paths.append(prefix)

        if extra_paths:
            # Flags are one CLI arg each and do not need quotes.
            ps = ['-I%s/include' % p for p in extra_paths]
            arguments.append('CFLAGS=%s' % ' '.join(ps))
            ps = ['-L%s/lib' % p for p in extra_paths]
            arguments.append('LDFLAGS=%s' % ' '.join(ps))
        return arguments

    def get_package_prefix(self, name):
        if sys.platform == 'darwin':
            cmd = ['brew', '--prefix', name]
        else:
            self.logger.error("ERROR: package-only libraries"
                              " are not supported on %s" % sys.platform)
            sys.exit(1)

        stdout = self.get_output(*cmd)
        self.logger.error("Package prefix for %s is '%s'" % (name, stdout))
        return stdout

    def download(self, url, filename):
        self.logger.error("Download %s into %s" % (url, filename))
        download(url, filename)

    def _install_pip(self):
        # On Python: 3.5a0 <= version < 3.5.0 (final), install pip 7.1.2,
        # the last version working on Python 3.5a0:
        # https://sourceforge.net/p/pyparsing/bugs/100/
        force_old_pip = (0x30500a0 <= self.hexversion < 0x30500f0)

        # is pip already installed and working?
        exitcode = self.run_nocheck(self.program, '-u', '-m', 'pip', '--version')
        if not exitcode:
            if force_old_pip:
                self.run(self.program, '-u', '-m', 'pip', 'install', REQ_OLD_PIP)
            else:
                # Upgrade pip
                self.run(self.program, '-u', '-m', 'pip', 'install', '-U', 'pip')
            return

        # pip is missing (or broken?): install it
        filename = os.path.join(self.conf.directory, 'get-pip.py')
        if not os.path.exists(filename):
            self.download(GET_PIP_URL, filename)

        if force_old_pip:
            self.run(self.program, '-u', filename, REQ_OLD_PIP)
        else:
            # Install pip
            self.run(self.program, '-u', filename)

    def install_pip(self):
        self._install_pip()

        # Dump the pip version
        self.run(self.program, '-u', '-m', 'pip', '--version')

    def install_performance(self):
        cmd = [self.program, '-u', '-m', 'pip', 'install']

        if is_build_dir():
            root_dir = os.path.dirname(PERFORMANCE_ROOT)
            cmd.extend(('-e', root_dir))
        else:
            version = pyperformance.__version__
            cmd.append('pyperformance==%s' % version)

        self.run(*cmd)

    def compile_install(self):
        self.compile()
        self.install_python()
        self.get_version()
        self.install_pip()
        self.install_performance()


class BenchmarkRevision(Application):

    _dryrun = False

    def __init__(self, conf, revision, branch=None, patch=None,
                 setup_log=True, filename=None, commit_date=None,
                 options=None):
        super().__init__(conf, options)
        self.patch = patch
        self.exitcode = 0
        self.uploaded = False

        if setup_log:
            if branch:
                prefix = 'compile-%s-%s' % (branch, revision)
            else:
                prefix = 'compile-%s' % revision
            self.setup_log(prefix)

        if filename is None:
            self.repository = Repository(self, conf.repo_dir)
            self.init_revision(revision, branch)
        else:
            # path used by cmd_upload()
            self.repository = None
            self.filename = filename
            self.revision = revision
            self.branch = branch
            self.commit_date = commit_date
            self.logger.error("Commit: branch=%s, revision=%s"
                              % (self.branch, self.revision))

        self.upload_filename = os.path.join(self.conf.uploaded_json_dir,
                                            os.path.basename(self.filename))

    def init_revision(self, revision, branch=None):
        if self.conf.update:
            self.repository.fetch()

        if branch:
            is_branch, rev_name, full_revision = self.repository.parse_revision(branch)
            if not is_branch:
                self.logger.error("ERROR: %r is not a Git branch" % self.branch)
                sys.exit(1)
            self.branch = branch
        else:
            self.branch = None

        is_branch, rev_name, full_revision = self.repository.parse_revision(revision)
        if is_branch:
            if self.branch and revision != self.branch:
                raise ValueError("inconsistenct branches: "
                                 "revision=%r, branch=%r"
                                 % (revision, branch))
            self.branch = revision
        elif not self.branch:
            self.branch = DEFAULT_BRANCH

        self.revision, date = self.repository.get_revision_info(rev_name)
        self.logger.error("Commit: branch=%s, revision=%s, date=%s"
                          % (self.branch, self.revision, date))
        self.commit_date = date

        date = date.strftime('%Y-%m-%d_%H-%M')

        filename = '%s-%s-%s' % (date, self.branch, self.revision[:12])
        if self.patch:
            patch = os.path.basename(self.patch)
            patch = os.path.splitext(patch)[0]
            filename = "%s-patch-%s" % (filename, patch)
        filename = filename + ".json.gz"
        if self.patch:
            self.filename = os.path.join(self.conf.json_patch_dir, filename)
        else:
            self.filename = os.path.join(self.conf.json_dir, filename)

    def compile_install(self):
        self.repository.checkout(self.revision)

        # First: remove everything
        self.safe_rmdir(self.conf.build_dir)
        self.safe_rmdir(self.conf.prefix)
        self.safe_rmdir(self.conf.venv)

        self.python.patch(self.patch)
        self.python.compile_install()

    def create_venv(self):
        # Create venv
        python = self.python.program
        if self._dryrun:
            program, exists = resolve_python(
                self.conf.prefix if self.conf.install else None,
                self.conf.build_dir,
            )
            if not python or not exists:
                python = sys.executable
        cmd = [python, '-u', '-m', 'pyperformance', 'venv', 'recreate',
               '--benchmarks', '<NONE>']
        if self.conf.venv:
            cmd.extend(('--venv', self.conf.venv))
        if self.options.inherit_environ:
            cmd.append('--inherit-environ=%s' % ','.join(self.options.inherit_environ))
        exitcode = self.run_nocheck(*cmd)
        if exitcode:
            sys.exit(EXIT_VENV_ERROR)

    def run_benchmark(self):
        self.safe_makedirs(os.path.dirname(self.filename))
        python = self.python.program
        if self._dryrun:
            python = sys.executable
        cmd = [python, '-u',
               '-m', 'pyperformance',
               'run',
               '--verbose',
               '--output', self.filename]
        if self.options.inherit_environ:
            cmd.append('--inherit-environ=%s' % ','.join(self.options.inherit_environ))
        if self.conf.manifest:
            cmd.extend(('--manifest', self.conf.manifest))
        if self.conf.benchmarks:
            cmd.append('--benchmarks=%s' % self.conf.benchmarks)
        if self.conf.affinity:
            cmd.extend(('--affinity', self.conf.affinity))
        if self.conf.venv:
            cmd.extend(('--venv', self.conf.venv))
        if self.conf.debug:
            cmd.append('--debug-single-value')
        exitcode = self.run_nocheck(*cmd)

        if os.path.exists(self.filename):
            self.update_metadata()

        return bool(exitcode)

    def update_metadata(self):
        metadata = {
            'commit_id': self.revision,
            'commit_branch': self.branch,
            'commit_date': self.commit_date.isoformat(),
        }
        if self.patch:
            metadata['patch_file'] = self.patch

        suite = pyperf.BenchmarkSuite.load(self.filename)
        for bench in suite:
            bench.update_metadata(metadata)
        suite.dump(self.filename, replace=True)

    def encode_benchmark(self, bench):
        data = {}
        data['environment'] = self.conf.environment
        data['project'] = self.conf.project
        data['branch'] = self.branch
        data['benchmark'] = bench.get_name()
        # Other benchmark metadata:
        # - description
        # - units="seconds", units_title="Time", lessisbetter=True
        data['commitid'] = self.revision
        data['revision_date'] = self.commit_date.isoformat()
        data['executable'] = self.conf.executable
        data['result_value'] = bench.mean()
        # Other result metadata: result_date
        if bench.get_nvalue() == 1:
            data['std_dev'] = 0
        else:
            data['std_dev'] = bench.stdev()
        values = bench.get_values()
        data['min'] = min(values)
        data['max'] = max(values)
        # Other stats metadata: q1, q3
        return data

    def upload(self):
        if self.uploaded:
            raise Exception("already uploaded")

        if self.filename == self.upload_filename:
            self.logger.error("ERROR: %s was already uploaded!"
                              % self.filename)
            sys.exit(1)

        if os.path.exists(self.upload_filename):
            self.logger.error("ERROR: cannot upload, %s file ready exists!"
                              % self.upload_filename)
            sys.exit(1)

        self.safe_makedirs(self.conf.uploaded_json_dir)

        suite = pyperf.BenchmarkSuite.load(self.filename)
        data = [self.encode_benchmark(bench)
                for bench in suite]
        data = dict(json=json.dumps(data))

        url = self.conf.url
        if not url.endswith('/'):
            url += '/'
        url += 'result/add/json/'
        self.logger.error("Upload %s benchmarks to %s" % (len(suite), url))

        try:
            response = urlopen(data=urlencode(data).encode('utf-8'), url=url)
            body = response.read()
            response.close()
        except HTTPError as err:
            self.logger.error("HTTP Error: %s" % err)
            errmsg = err.read().decode('utf8')
            self.logger.error(errmsg)
            err.close()
            return

        self.logger.error('Response: "%s"' % body.decode('utf-8'))

        self.logger.error("Move %s to %s"
                          % (self.filename, self.upload_filename))
        os.rename(self.filename, self.upload_filename)

        self.uploaded = True

    def perf_system_tune(self):
        pythonpath = os.environ.get('PYTHONPATH')
        args = ['-m', 'pyperf', 'system', 'tune']
        if self.conf.affinity:
            args.extend(('--affinity', self.conf.affinity))
        if pythonpath:
            cmd = ('PYTHONPATH=%s %s %s'
                   % (shlex.quote(pythonpath),
                      shlex.quote(sys.executable),
                      ' '.join(args)))
            self.run('sudo', 'bash', '-c', cmd)
        else:
            self.run('sudo', sys.executable, *args)

    def prepare(self):
        self.logger.error("Compile and benchmarks Python rev %s (branch %s)"
                          % (self.revision, self.branch))
        self.logger.error('')

        if os.path.exists(self.filename):
            filename = self.filename
        elif self.conf.upload and os.path.exists(self.upload_filename):
            filename = self.upload_filename
        else:
            filename = False
        if filename:
            # Benchmark already uploaded
            self.logger.error("JSON file %s already exists: do nothing"
                              % filename)

            # Remove the log file
            if self.log_filename:
                self.logger.error("Remove log file %s" % self.log_filename)
                del self.logger.handlers[:]
                os.unlink(self.log_filename)

            sys.exit(EXIT_ALREADY_EXIST)

        if self.log_filename:
            self.logger.error("Write logs into %s" % self.log_filename)

        if self.patch and self.conf.upload:
            self.logger.error("Disable upload on patched Python")
            self.conf.upload = False

        if self.conf.debug and self.conf.upload:
            self.logger.error("Disable upload in debug mode")
            self.conf.upload = False

        if not self.conf.install and self.conf.upload:
            self.logger.error("Disable upload if Python is not installed")
            self.conf.upload = False

        if self.conf.system_tune:
            self.perf_system_tune()

    def compile_bench(self):
        self.python = Python(self, self.conf)

        if not self._dryrun:
            try:
                self.compile_install()
            except SystemExit:
                sys.exit(EXIT_COMPILE_ERROR)

        self.create_venv()

        failed = self.run_benchmark()
        if not failed and self.conf.upload:
            self.upload()
        return failed

    def main(self):
        self.start = time.monotonic()

        self.prepare()
        failed = self.compile_bench()

        dt = time.monotonic() - self.start
        dt = datetime.timedelta(seconds=dt)
        self.logger.error("Benchmark completed in %s" % dt)

        if self.uploaded:
            self.logger.error("Benchmark results uploaded and written into %s"
                              % self.upload_filename)
        elif failed:
            self.logger.error("Benchmark failed but results written into %s"
                              % self.filename)
        else:
            self.logger.error("Benchmark result written into %s"
                              % self.filename)

        if failed:
            sys.exit(EXIT_BENCH_ERROR)


class Configuration:
    pass


def parse_config(filename, command):
    parse_compile = False
    parse_compile_all = False
    if command == 'compile_all':
        parse_compile = True
        parse_compile_all = True
    elif command == 'compile':
        parse_compile = True
    else:
        assert command == 'upload'

    conf = Configuration()
    cfgobj = configparser.ConfigParser()
    cfgobj.read(filename)

    def getstr(section, key, default=None):
        try:
            sectionobj = cfgobj[section]
            value = sectionobj[key]
        except KeyError:
            if default is None:
                raise
            return default

        # strip comments
        value = value.partition('#')[0]
        # strip spaces
        return value.strip()

    def getfile(section, key, default=None):
        value = getstr(section, key, default)
        if not value:
            return value
        value = os.path.expanduser(value)
        return value

    def getboolean(section, key, default):
        try:
            sectionobj = cfgobj[section]
            return sectionobj.getboolean(key, default)
        except KeyError:
            return default

    # [config]
    conf.json_dir = getfile('config', 'json_dir')
    conf.json_patch_dir = os.path.join(conf.json_dir, 'patch')
    conf.uploaded_json_dir = os.path.join(conf.json_dir, 'uploaded')
    conf.debug = getboolean('config', 'debug', False)

    if parse_compile:
        # [scm]
        conf.repo_dir = getfile('scm', 'repo_dir')
        conf.update = getboolean('scm', 'update', True)
        conf.git_remote = getstr('config', 'git_remote', default='remotes/origin')

        # [compile]
        conf.directory = getfile('compile', 'bench_dir')
        conf.lto = getboolean('compile', 'lto', True)
        conf.pgo = getboolean('compile', 'pgo', True)
        conf.install = getboolean('compile', 'install', True)
        conf.pkg_only = getstr('compile', 'pkg_only', '').split()

        # [run_benchmark]
        conf.system_tune = getboolean('run_benchmark', 'system_tune', True)
        conf.manifest = getfile('run_benchmark', 'manifest')
        conf.benchmarks = getstr('run_benchmark', 'benchmarks', default='')
        conf.affinity = getstr('run_benchmark', 'affinity', default='')
        conf.upload = getboolean('run_benchmark', 'upload', False)

        # paths
        conf.build_dir = os.path.join(conf.directory, 'build')
        conf.prefix = os.path.join(conf.directory, 'prefix')
        conf.venv = os.path.join(conf.directory, 'venv')

        check_upload = conf.upload
    else:
        check_upload = True

    # [upload]
    UPLOAD_OPTIONS = ('url', 'environment', 'executable', 'project')

    conf.url = getstr('upload', 'url', default='')
    conf.executable = getstr('upload', 'executable', default='')
    conf.project = getstr('upload', 'project', default='')
    conf.environment = getstr('upload', 'environment', default='')

    if check_upload and any(not getattr(conf, attr) for attr in UPLOAD_OPTIONS):
        print("ERROR: Upload requires to set the following "
              "configuration option in the the [upload] section "
              "of %s:"
              % filename)
        for attr in UPLOAD_OPTIONS:
            text = "- %s" % attr
            if not getattr(conf, attr):
                text += " (not set)"
            print(text)
        sys.exit(1)

    if parse_compile_all:
        # [compile_all]
        conf.branches = getstr('compile_all', 'branches', '').split()
        conf.revisions = []
        try:
            revisions = cfgobj.items('compile_all_revisions')
        except configparser.NoSectionError:
            pass
        else:
            for revision, name in revisions:
                # strip comments
                name = name.partition('#')[0]
                # strip spaces
                name = name.strip()
                conf.revisions.append((revision, name))

    # process config
    if conf.debug:
        conf.pgo = False
        conf.lto = False

    return conf


class BenchmarkAll(Application):
    def __init__(self, config_filename, options):
        config_filename = os.path.abspath(config_filename)
        conf = parse_config(config_filename, "compile_all")
        super().__init__(conf, options)
        self.config_filename = config_filename
        self.safe_makedirs(self.conf.directory)
        self.setup_log('compile_all')
        self.outputs = []
        self.skipped = []
        self.uploaded = []
        self.failed = []
        self.timings = []
        self.logger = logging.getLogger()

    def benchmark(self, revision, branch):
        if branch:
            key = '%s-%s' % (branch, revision)
        else:
            key = revision

        cmd = [sys.executable, '-m', 'pyperformance', 'compile',
               self.config_filename, revision, branch]
        if not self.conf.update:
            cmd.append('--no-update')
        if not self.conf.system_tune:
            cmd.append('--no-tune')

        self.start = time.monotonic()
        exitcode = self.run_nocheck(*cmd, log_stdout=False)
        dt = time.monotonic() - self.start

        if exitcode:
            self.logger.error("Benchmark exit code: %s" % exitcode)

        if exitcode == EXIT_ALREADY_EXIST:
            # Benchmark already uploaded
            self.skipped.append(key)
            return

        # compile, venv and bench errors occur after repository update
        # and system tune
        if exitcode >= EXIT_COMPILE_ERROR:
            if self.conf.system_tune:
                # only tune the system once
                self.conf.system_tune = False

            if self.conf.update:
                # Ony update the repository once
                self.conf.update = False

        if exitcode == 0:
            if self.conf.upload:
                self.uploaded.append(key)
            else:
                self.outputs.append(key)
            self.timings.append(dt)
        else:
            self.failed.append(key)

    def report(self):
        for key in self.skipped:
            self.logger.error("Skipped: %s" % key)

        for key in self.outputs:
            self.logger.error("Tested: %s" % key)

        for key in self.uploaded:
            self.logger.error("Tested and uploaded: %s" % key)

        for key in self.failed:
            text = "FAILED: %s" % key
            self.logger.error(text)

    def report_timings(self):
        def format_time(seconds):
            if seconds >= 100:
                return "%.0f min %.0f sec" % divmod(seconds, 60)
            else:
                return "%.0f sec" % math.ceil(seconds)

        self.logger.error("Timings:")
        self.logger.error("- min: %s" % format_time(min(self.timings)))
        text = "- avg: %s" % format_time(statistics.mean(self.timings))
        if len(self.timings) >= 2:
            stdev = statistics.stdev(self.timings)
            text = "%s -- std dev: %s" % (text, format_time(stdev))
        self.logger.error(text)
        self.logger.error("- max: %s" % format_time(max(self.timings)))

    def main(self):
        self.safe_makedirs(self.conf.directory)

        self.logger.error("Compile and benchmark all")
        if self.log_filename:
            self.logger.error("Write logs into %s" % self.log_filename)
        self.logger.error("Revisions: %r" % (self.conf.revisions,))
        self.logger.error("Branches: %r" % (self.conf.branches,))

        if not self.conf.revisions and not self.conf.branches:
            self.logger.error("ERROR: no branches nor revisions "
                              "configured for compile_all")
            sys.exit(1)

        try:
            for revision, branch in self.conf.revisions:
                self.benchmark(revision, branch)

            for branch in self.conf.branches:
                self.benchmark(branch, branch)
        finally:
            self.report()
            if self.timings:
                self.report_timings()

        if self.failed:
            sys.exit(1)


def cmd_compile(options):
    conf = parse_config(options.config_file, "compile")
    if options is not None:
        if options.no_update:
            conf.update = False
        if options.no_tune:
            conf.system_tune = False
        if options.venv:
            conf.venv = options.venv
    bench = BenchmarkRevision(conf, options.revision, options.branch,
                              patch=options.patch, options=options)
    bench.main()


def cmd_upload(options):
    conf = parse_config(options.config_file, "upload")

    filename = options.json_file
    bench = pyperf.BenchmarkSuite.load(filename)
    metadata = bench.get_metadata()
    revision = metadata['commit_id']
    branch = metadata['commit_branch']
    commit_date = parse_date(metadata['commit_date'])

    bench = BenchmarkRevision(conf, revision, branch,
                              filename=filename, commit_date=commit_date,
                              setup_log=False, options=options)
    bench.upload()


def cmd_compile_all(options):
    bench = BenchmarkAll(options.config_file, options=options)
    bench.main()
