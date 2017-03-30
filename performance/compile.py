import configparser
import datetime
import errno
import json
import logging
import os.path
import perf
import shlex
import shutil
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

from performance.venv import GET_PIP_URL


GIT = True
DEFAULT_BRANCH = 'master' if GIT else 'default'
LOG_FORMAT = '%(asctime)-15s: %(message)s'


class Repository(object):
    def __init__(self, app, path):
        self.path = path
        self.logger = app.logger
        self.app = app

    def get_output(self, *cmd):
        return self.app.get_output(*cmd, cwd=self.path)

    def run(self, *cmd, **kw):
        self.app.run(*cmd, cwd=self.path, **kw)

    def fetch(self):
        if GIT:
            self.run('git', 'fetch')
        else:
            self.run('hg', 'pull')

    def get_branch(self):
        stdout = self.get_output('git', 'branch')
        for line in stdout.splitlines():
            if line.startswith('* '):
                branch = line[2:]
                self.logger.error('Git branch: %r' % branch)
                return branch

        self.logger.error("ERROR: fail to get the current Git branch")
        sys.exit(1)

    def checkout(self, revision):
        if GIT:
            # remove all untracked files
            self.run('git', 'clean', '-fdx')

            # checkout to requested revision
            self.run('git', 'reset', '--hard', 'HEAD')
            self.run('git', 'checkout', revision)

            branch = self.get_branch()
            if revision == branch:
                # revision is a branch
                self.run('git', 'merge', '--ff')

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
            # drop second and timezone
            date = datetime.datetime.strptime(date[:16], '%Y-%m-%d %H:%M')
        else:
            node, date = stdout.split('|')
            date = datetime.datetime.strptime(date[:16], '%Y-%m-%d %H:%M')
        return (node, date)


class Application(object):
    def __init__(self):
        logging.basicConfig(format=LOG_FORMAT)
        self.logger = logging.getLogger()

    def setup_log(self):
        self.safe_makedirs(os.path.dirname(self.conf.log))

        handler = logging.FileHandler(self.conf.log)
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
        try:
            proc = self.create_subprocess(cmd,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT,
                                          universal_newlines=True,
                                          **kwargs)

            # FIXME: support Python 2?
            with proc:
                for line in proc.stdout:
                    line = line.rstrip()
                    self.logger.error(line)
                exitcode = proc.wait()
        finally:
            if stdin_file is not None:
                stdin_file.close()

        return exitcode

    def run(self, *cmd, **kw):
        exitcode = self.run_nocheck(*cmd, **kw)
        if exitcode:
            sys.exit(exitcode)

    def get_output(self, *cmd, **kwargs):
        proc = self.create_subprocess(cmd,
                                      stdout=subprocess.PIPE,
                                      universal_newlines=True,
                                      **kwargs)
        # FIXME: support Python 2?
        with proc:
            stdout = proc.communicate()[0]

        exitcode = proc.wait()
        if exitcode:
            self.logger.error(stdout, end='')
            sys.exit(exitcode)

        return stdout

    def safe_makedirs(self, directory):
        try:
            os.makedirs(directory)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise


class Python(object):
    def __init__(self, app, conf):
        self.app = app
        self.conf = conf
        self.logger = app.logger
        self.cwd = conf.repo_dir
        self.program = None

    def run_nocheck(self, *cmd, **kw):
        return self.app.run_nocheck(*cmd, cwd=self.cwd, **kw)

    def run(self, *cmd, **kw):
        self.app.run(*cmd, cwd=self.cwd, **kw)

    def patch(self, filename):
        if not filename:
            return

        self.logger.error('Apply patch %s on revision %s'
                          % (filename, self.app.revision))
        self.run('patch', '-p1', stdin_filename=filename)

    def compile(self):
        self.run_nocheck('make', 'distclean')

        config_args = []
        if self.conf.debug:
            config_args.append('--with-pydebug')
        elif self.conf.lto:
            config_args.append('--with-lto')
        if self.conf.prefix:
            config_args.extend(('--prefix', self.conf.prefix))
        if self.conf.debug:
            config_args.append('CFLAGS=-O0')
        self.run('./configure', *config_args)

        self.run_nocheck('make', 'clean')

        if self.conf.pgo:
            # FIXME: use taskset (isolated CPUs) for PGO?
            self.run('make', 'profile-opt')
        else:
            self.run('make')

    def install_python(self):
        prefix = self.conf.prefix

        if sys.platform in ('darwin', 'win32'):
            program_ext = '.exe'
        else:
            program_ext = ''

        if not prefix:
            # don't install: run python from the compilation directory
            self.program = "./python" + program_ext
            return

        if os.path.exists(prefix):
            self.logger.error("Remove directory %s" % prefix)
            shutil.rmtree(prefix)

        self.app.safe_makedirs(self.conf.directory)
        self.run('make', 'install')

        self.program = os.path.join(prefix, "bin", "python" + program_ext)
        if not os.path.exists(self.program):
            self.program = os.path.join(prefix, "bin", "python3" + program_ext)

    def install_performance(self):
        exitcode = self.run_nocheck(self.program, '-u', '-m', 'pip', '--version')
        if exitcode:
            # pip is missing (or broken?): install it
            self.run('wget', GET_PIP_URL, '-O', 'get-pip.py')
            self.run(self.program, '-u', 'get-pip.py')

        # Install performance
        self.run(self.program, '-u', '-m', 'pip', 'install', '-U', 'performance')


class BenchmarkRevision(Application):
    def __init__(self, conf, revision, branch, patch=None, setup_log=False,
                 filename=None):
        super().__init__()
        self.conf = conf
        self.branch = branch
        self.patch = patch
        self.uploaded = False

        if setup_log and self.conf.log:
            self.setup_log()

        if filename is None:
            self.repository = Repository(self, conf.repo_dir)
            self.init_revision_filenename(revision)
        else:
            # path used by cmd_upload()
            self.repository = None
            self.filename = filename
            self.revision = revision

        self.upload_filename = os.path.join(self.conf.uploaded_json_dir,
                                            os.path.basename(self.filename))

    def init_revision_filenename(self, revision):
        self.revision, date = self.repository.get_revision_info(revision)
        date = date.strftime('%Y-%m-%d_%H-%M')

        filename = '%s-%s-%s' % (date, self.branch, self.revision[:12])
        if self.patch:
            patch = os.path.splitext(self.patch)[0]
            filename = "%s-patch-%s" % (filename, patch)
        filename = filename + ".json.gz"
        if self.patch:
            self.filename = os.path.join(self.conf.json_patch_dir, filename)
        else:
            self.filename = os.path.join(self.conf.json_dir, filename)

    def compile_install(self):
        if self.conf.update:
            self.repository.fetch()
        self.repository.checkout(self.revision)

        self.python.patch(self.patch)

        self.python.compile()

        self.python.install_python()

        self.python.install_performance()

    def run_benchmark(self):
        self.safe_makedirs(os.path.dirname(self.filename))

        # Create venv
        cmd = [self.python.program, '-u', '-m', 'performance',
               'venv', 'recreate']
        if self.conf.venv:
            cmd.extend(('--venv', self.conf.venv))
        self.run(*cmd)

        cmd = [self.python.program, '-u',
               '-m', 'performance',
               'run',
               '--verbose',
               '--benchmarks', self.conf.benchmarks,
               '--output', self.filename]
        if self.conf.affinity:
            cmd.extend(('--affinity', self.conf.affinity))
        if self.conf.venv:
            cmd.extend(('--venv', self.conf.venv))
        if self.conf.debug:
            cmd.append('--debug-single-value')
        self.run(*cmd)

        self.update_metadata()

    def update_metadata(self):
        if GIT:
            metadata = {'git_branch': self.branch, 'git_revision': self.revision}
        else:
            metadata = {'hg_branch': self.branch, 'hg_revision': self.revision}
        if self.patch:
            metadata['patch_file'] = self.patch

        suite = perf.BenchmarkSuite.load(self.filename)
        for bench in suite:
            bench.update_metadata(metadata)
        suite.dump(self.filename, replace=True)

    def encode_benchmark(self, bench):
        data = {}
        data['benchmark'] = bench.get_name()
        data['result_value'] = bench.mean()

        values = bench.get_values()
        data['min'] = min(values)
        data['max'] = max(values)
        if self.conf.debug and bench.get_nvalue() == 1:
            # only allow to upload 1 point in debug mode
            data['std_dev'] = 0
        else:
            data['std_dev'] = bench.stdev()

        data['executable'] = self.conf.executable
        data['commitid'] = self.revision
        data['branch'] = self.branch
        data['project'] = self.conf.project
        data['environment'] = self.conf.environment
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

        suite = perf.BenchmarkSuite.load(self.filename)
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

    def sanity_checks(self):
        if self.conf.debug and self.conf.upload:
            self.logger.error("ERROR: debug mode is incompatible with upload")
            sys.exit(1)

        # FIXME: support run without prefix?
        if not self.conf.prefix:
            self.logger.error("ERROR: running benchmark without installation "
                              "is currently broken")
            sys.exit(1)

        if os.path.exists(self.filename):
            self.logger.error("ERROR: %s file already exists!"
                              % self.filename)
            sys.exit(1)

        if self.conf.upload and os.path.exists(self.upload_filename):
            self.logger.error("ERROR: cannot upload, %s file already exists!"
                              % self.upload_filename)
            sys.exit(1)

    def perf_system_tune(self):
        pythonpath = os.environ.get('PYTHONPATH')
        args = ['-m', 'perf', 'system', 'tune']
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

    def main(self):
        self.start = time.monotonic()

        self.logger.error("Compile and benchmarks Python rev %s (branch %s)"
                          % (self.revision, self.branch))
        self.logger.error('')
        if self.conf.log:
            self.logger.error("Write logs into %s" % self.conf.log)

        if self.patch:
            # Don't upload resuls of patched Python
            self.conf.upload = False
        self.sanity_checks()
        if self.conf.tune:
            self.perf_system_tune()

        self.python = Python(self, self.conf)
        self.compile_install()
        self.run_benchmark()
        if self.conf.upload:
            self.upload()

        dt = time.monotonic() - self.start
        dt = datetime.timedelta(seconds=dt)
        self.logger.error("Benchmark completed in %s" % dt)

        if self.uploaded:
            self.logger.error("Benchmark result uploaded and written into %s"
                              % self.filename)
        else:
            self.logger.error("Benchmark result written into %s"
                              % self.filename)


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
            value = default
        return value.strip()

    def getboolean(section, key, default):
        try:
            sectionobj = cfgobj[section]
            return sectionobj.getboolean(key, default)
        except KeyError:
            return default

    # [config]
    conf.json_dir = os.path.expanduser(getstr('config', 'json_dir'))
    conf.json_patch_dir = os.path.join(conf.json_dir, 'patch')
    conf.uploaded_json_dir = os.path.join(conf.json_dir, 'uploaded')
    conf.debug = getboolean('config', 'debug', False)

    if parse_compile:
        # [scm]
        conf.repo_dir = os.path.expanduser(getstr('scm', 'repo_dir'))
        conf.update = getboolean('scm', 'update', True)
        conf.git_remote = getstr('config', 'git_remote', default='remotes/origin')

        # [compile]
        conf.directory = os.path.expanduser(getstr('compile', 'bench_dir'))
        conf.lto = getboolean('compile', 'lto', True)
        conf.pgo = getboolean('compile', 'pgo', True)

        # [run_benchmark]
        conf.tune = getboolean('run_benchmark', 'tune', True)
        conf.benchmarks = getstr('run_benchmark', 'benchmarks', default='default')
        conf.affinity = getstr('run_benchmark', 'affinity', default='')
        conf.upload = getboolean('run_benchmark', 'upload', False)

        # paths
        conf.prefix = os.path.join(conf.directory, 'prefix')
        conf.venv = os.path.join(conf.directory, 'venv')
        # FIXME: create a different log file at each run
        conf.log = os.path.join(conf.directory, 'bench.log')

    # [upload]
    UPLOAD_OPTIONS = ('url', 'environment', 'executable', 'project')

    conf.url = getstr('upload', 'url', default='')
    conf.executable = getstr('upload', 'executable', default='')
    conf.project = getstr('upload', 'project', default='')
    conf.environment = getstr('upload', 'environment', default='')

    if any(not getattr(conf, attr) for attr in UPLOAD_OPTIONS):
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
                conf.revisions.append((revision, name))

    # process config
    if conf.debug:
        conf.pgo = False
        conf.lto = False

    return conf


class BenchmarkAll(Application):
    def __init__(self, config_filename):
        super().__init__()
        self.conf = parse_config(config_filename, "compile_all")
        self.safe_makedirs(self.conf.directory)
        if self.conf.log:
            self.setup_log()
        self.outputs = []
        self.skipped = []
        self.uploaded = []
        self.failed = []
        self.logger = logging.getLogger()
        self.updated = False

    def benchmark(self, revision, branch):
        bench = BenchmarkRevision(self.conf, revision, branch,
                                  setup_log=False)
        if os.path.exists(bench.upload_filename):
            # Benchmark already uploaded
            self.skipped.append(bench.upload_filename)
            return

        if self.conf.tune:
            bench.perf_system_tune()
            # only tune the system once
            self.conf.tune = False

        if self.conf.update:
            bench.repository.fetch()
            # Ony update the repository once
            self.conf.update = False

        try:
            bench.main()
        except SystemExit:
            self.failed.append(bench.filename)
            return

        if bench.uploaded:
            self.uploaded.append(bench.upload_filename)
        else:
            self.outputs.append(bench.filename)

    def main(self):
        self.safe_makedirs(self.conf.directory)

        try:
            for revision, branch in self.conf.revisions:
                self.benchmark(revision, branch or DEFAULT_BRANCH)

            for branch in self.conf.branches:
                if GIT:
                    revision = '%s/%s' % (self.conf.git_remote, branch)
                else:
                    revision = branch
                self.benchmark(revision, branch)
        finally:
            for filename in self.skipped:
                self.logger.error("Skipped: %s" % filename)

            for filename in self.outputs:
                self.logger.error("Tested: %s" % filename)

            for filename in self.uploaded:
                self.logger.error("Tested and uploaded: %s" % filename)

            for filename in self.failed:
                self.logger.error("FAILED: %s" % filename)


def cmd_compile(options):
    conf = parse_config(options.config_file, "compile")
    bench = BenchmarkRevision(conf, options.revision, options.branch,
                              patch=options.patch)
    bench.main()


def cmd_upload(options):
    conf = parse_config(options.config_file, "upload")

    filename = options.json_file
    bench = perf.BenchmarkSuite.load(filename)
    metadata = bench.get_metadata()
    try:
        revision = metadata['git_revision']
        branch = metadata['git_branch']
    except KeyError:
        revision = metadata['hg_revision']
        branch = metadata['hg_branch']

    bench = BenchmarkRevision(conf, revision, branch, filename=filename)
    bench.upload()


def cmd_compile_all(options):
    bench = BenchmarkAll(options.config_file)
    bench.main()
