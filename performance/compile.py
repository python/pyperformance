import configparser
import datetime
import errno
import json
import logging
import os.path
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

    def run(self, *cmd):
        self.app.run(*cmd, cwd=self.path)

    def fetch(self):
        if GIT:
            self.run('git', 'fetch')
        else:
            self.run('hg', 'pull')

    def get_branch(self):
        stdout = self.get_output('git', 'branch')
        for line in stdout.splitlines():
            if line.startswith('* '):
                return line[2:]
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

    def get_revision(self):
        if GIT:
            revision = self.get_output('git', 'show', '-s',
                                       '--pretty=format:%H')
        else:
            revision = self.get_output('hg', 'id', '-i')
        revision = revision.strip()
        if not revision:
            self.logger.error("ERROR: unable to get the revision")
            sys.exit(1)
        return revision

    def get_revision_info(self, revision):
        if GIT:
            cmd = ['git', 'log', '--format=%H|%ci', '%s^!' % revision]
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
        handler = logging.FileHandler(self.conf.log)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def create_subprocess(self, cmd, **kwargs):
        self.logger.error("+ %s" % ' '.join(cmd))
        return subprocess.Popen(cmd, **kwargs)

    def run_nocheck(self, *cmd, stdin_filename=None, **kwargs):
        if stdin_filename:
            stdin_file = open(stdin_filename, "rb", 0)
            fd = stdin_file.fileno()
            kwargs = {'stdin': fd, 'pass_fds': [fd]}
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


class BenchmarkPython(Application):
    def __init__(self, conf, revision, branch, patch=None, setup_log=False):
        super().__init__()
        self.conf = conf
        self.branch = branch
        self.patch = patch
        self.python = None
        self.uploaded = False

        self.safe_makedirs(self.conf.directory)
        self.safe_makedirs(self.conf.json_directory)
        self.safe_makedirs(self.conf.uploaded_json_dir)

        if setup_log and self.conf.log:
            self.setup_log()

        self.repository = Repository(self, conf.cpython_srcdir)

        self.revision, date = self.repository.get_revision_info(revision)
        date = date.strftime('%Y-%m-%d_%H-%M')

        filename = '%s-%s-%s' % (date, branch, self.revision[:12])
        filename = filename + ".json.gz"
        self.filename = os.path.join(self.conf.json_directory, filename)
        # FIXME: convert to a property to avoid inconsistencies if filename
        # is modified? see cmd_upload()
        self.upload_filename = os.path.join(self.conf.uploaded_json_dir,
                                            os.path.basename(filename))

    def prepare_code(self):
        self.logger.error('')
        text = "Benchmark CPython revision %s" % self.revision
        self.logger.error(text)
        self.logger.error("=" * len(text))
        self.logger.error('')

        if self.conf.update:
            self.repository.fetch()
        self.repository.checkout(self.revision)

        if self.patch:
            self.logger.error('Apply patch %s' % self.patch)
            self.run('patch', '-p1', stdin_filename=self.patch)

        full_revision = self.repository.get_revision()
        self.logger.error("Revision: %s" % full_revision)

    def compile(self):
        self.run_nocheck('make', 'distclean')

        config_args = []
        if self.conf.debug:
            config_args.append('--with-pydebug')
        elif self.conf.lto:
            config_args.append('--with-lto')
        if self.conf.prefix:
            config_args.extend(('--prefix', self.conf.prefix))
        self.run('./configure', *config_args)

        self.run_nocheck('make', 'clean')

        if self.conf.pgo:
            # FIXME: use taskset (isolated CPUs) for PGO?
            self.run('make', 'profile-opt')
        else:
            self.run('make')

    def rmtree(self, directory):
        if not os.path.exists(directory):
            return

        self.logger.error("Remove directory %s" % directory)
        shutil.rmtree(directory)

    def install(self):
        prefix = self.conf.prefix

        if sys.platform in ('darwin', 'win32'):
            program_ext = '.exe'
        else:
            program_ext = ''

        if prefix:
            self.rmtree(prefix)

            self.run('make', 'install')

            self.python = os.path.join(prefix, "bin", "python" + program_ext)
            if not os.path.exists(self.python):
                self.python = os.path.join(prefix, "bin", "python3" + program_ext)
        else:
            self.python = "./python" + program_ext

        exitcode = self.run_nocheck(self.python, '-u', '-m', 'pip', '--version')
        if exitcode:
            # pip is missing (or broken?): install it
            self.run('wget', GET_PIP_URL, '-O', 'get-pip.py')
            self.run(self.python, '-u', 'get-pip.py')

        # Install performance
        self.run(self.python, '-u', '-m', 'pip', 'install', '-U', 'performance')

    def run_benchmark(self):
        # Create venv
        cmd = [self.python, '-u', '-m', 'performance', 'venv', 'recreate']
        if self.conf.venv:
            cmd.extend(('--venv', self.conf.venv))
        self.run(*cmd)

        cmd = [self.python, '-u',
               '-m', 'performance',
               'run', '--verbose']
        cmd.extend(('--output', self.filename))
        if self.conf.venv:
            cmd.extend(('--venv', self.conf.venv))
        if self.conf.debug:
            cmd.append('--debug-single-value')
        self.run(*cmd)

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

        if os.path.exists(self.upload_filename):
            self.logger.error("ERROR: cannot upload, %s file ready exists!"
                              % self.upload_filename)
            sys.exit(1)

        # Import perf module from --perf directory
        sys.path.insert(0, self.conf.perf)

        import perf

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

    def main(self):
        self.start = time.monotonic()

        self.logger.error("Run benchmarks on Python %s" % self.revision)
        self.logger.error('')

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

        if self.conf.log:
            self.logger.error("Write logs into %s" % self.conf.log)

        self.logger.error("Move to %s" % self.conf.cpython_srcdir)
        # FIXME: don't rely on the current directory
        os.chdir(self.conf.cpython_srcdir)

        self.prepare_code()
        self.compile()
        self.install()
        self.run_benchmark()
        if self.conf.upload:
            self.upload()

        dt = time.monotonic() - self.start
        dt = datetime.timedelta(seconds=dt)
        self.logger.error("Benchmark completed in %s" % dt)

        return self.filename


def parse_config(filename):
    class Configuration:
        pass

    conf = Configuration()
    cfgobj = configparser.ConfigParser()
    cfgobj.read(filename)
    config = cfgobj['config']

    def getstr(section, key, default=None):
        try:
            sectionobj = cfgobj[section]
            value = sectionobj[key]
        except KeyError:
            if default is None:
                raise
            value = default
        return value.strip()

    conf.directory = os.path.expanduser(getstr('config', 'bench_root'))
    conf.json_directory = os.path.expanduser(getstr('config', 'json_dir'))
    conf.uploaded_json_dir = os.path.join(conf.json_directory, 'uploaded')
    conf.cpython_srcdir = os.path.expanduser(getstr('config', 'cpython_srcdir'))
    conf.perf = os.path.expanduser(getstr('config', 'perf_dir'))
    conf.prefix = os.path.join(conf.directory, 'prefix')
    conf.venv = os.path.join(conf.directory, 'venv')
    conf.log = os.path.join(conf.directory, 'bench.log')
    conf.lto = config.getboolean('lto', False)
    conf.pgo = config.getboolean('pgo', False)
    conf.branches = getstr('config', 'branches').split()
    conf.update = config.getboolean('update', True)
    conf.debug = config.getboolean('debug', False)
    conf.upload = config.getboolean('upload', False)

    if conf.debug:
        conf.pgo = False
        conf.lto = False

    if conf.upload:
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

    conf.revisions = []
    try:
        revisions = cfgobj.items('revisions')
    except configparser.NoSectionError:
        pass
    else:
        for revision, name in revisions:
            conf.revisions.append((revision, name))

    return conf


class BenchmarkAll(Application):
    def __init__(self, config_filename):
        super().__init__()
        self.conf = parse_config(config_filename)
        self.safe_makedirs(self.conf.directory)
        if self.conf.log:
            self.setup_log()
        self.outputs = []
        self.skipped = []
        self.uploaded = []
        self.failed = []
        self.logger = logging.getLogger()

    def benchmark(self, is_branch, revision):
        if is_branch:
            branch = revision
        else:
            branch = branch or DEFAULT_BRANCH

        bench = BenchmarkPython(self.conf, revision, branch, setup_log=False)
        if os.path.exists(bench.upload_filename):
            # Benchmark already uploaded
            self.skipped.append(bench.upload_filename)
            return
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
        self.run('sudo', 'python3', '-m', 'perf', 'system', 'tune',
                 cwd=self.conf.perf)

        self.repository = Repository(self, self.conf.cpython_srcdir)
        if self.conf.update:
            self.repository.fetch()

        try:
            for revision, branch in self.conf.revisions:
                self.benchmark(False, revision)

            for branch in self.conf.branches:
                self.benchmark(True, branch)
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
    conf = parse_config(options.config_file)
    bench = BenchmarkPython(conf, options.revision, options.branch,
                            patch=conf.patch)
    bench.main()


def cmd_upload(options):
    conf = parse_config(options.config_file)
    revision = options.revision
    branch = options.branch
    bench = BenchmarkPython(conf, revision, branch)
    bench.filename = options.json_file
    bench.upload_filename = os.path.join(conf.uploaded_json_dir,
                                         os.path.basename(bench.filename))
    bench.upload()


def cmd_compile_all(options):
    bench = BenchmarkAll(options.config_file)
    bench.main()
