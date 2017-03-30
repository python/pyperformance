import argparse
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
    # FIXME: make branch optional
    def __init__(self, conf, revision, branch=None, patch=None):
        super().__init__()
        self.conf = conf
        self.revision = revision
        self.patch = patch
        self.python = None

        self.safe_makedirs(self.conf.directory)
        self.safe_makedirs(self.conf.json_directory)
        self.safe_makedirs(self.conf.uploaded_json_dir)

        # FIXME: don't add multiple handlers when BenchmarkPython is created from Benchmark
        if self.conf.log:
            handler = logging.FileHandler(self.conf.log)
            formatter = logging.Formatter(LOG_FORMAT)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.repository = Repository(self, conf.cpython_srcdir)

        node, date = self.repository.get_revision_info(revision)
        short_node = node[:12]
        date = date.strftime('%Y-%m-%d_%H-%M')

        if branch:
            filename = '%s-%s-%s' % (date, branch, short_node)
        else:
            filename = '%s-%s' % (date, short_node)
        self.filename = os.path.join(self.conf.json_directory, filename + ".json.gz")

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

    def main(self):
        # FIXME
        if not self.conf.prefix:
            self.logger.error("ERROR: running benchmark without installation "
                              "is currently broken")
            sys.exit(1)

        if os.path.exists(self.filename):
            self.logger.error("ERROR: %s already exists" % self.filename)
            sys.exit(1)

        self.start = time.monotonic()

        self.logger.error("Run benchmarks")
        self.logger.error('')

        if self.conf.log:
            self.logger.error("Write logs into %s" % self.conf.log)

        self.logger.error("Move to %s" % self.conf.cpython_srcdir)
        # FIXME: don't rely on the current directory
        os.chdir(self.conf.cpython_srcdir)

        self.prepare_code()
        self.compile()
        self.install()
        self.run_benchmark()

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


class Benchmark(Application):
    def __init__(self):
        super().__init__()
        bench_dir = os.path.realpath(os.path.dirname(__file__))
        self.bench_cpython = os.path.join(bench_dir, 'bench_cpython.py')
        self.outputs = []
        self.skipped = []
        self.uploaded = []
        self.failed = []
        self.errors = []
        self.logger = logging.getLogger()

    def encode_benchmark(self, bench, branch, revision):
        data = {}
        data['benchmark'] = bench.get_name()
        data['result_value'] = bench.mean()

        values = bench.get_values()
        data['min'] = min(values)
        data['max'] = max(values)
        data['std_dev'] = bench.stdev()

        data['executable'] = self.conf.executable
        data['commitid'] = revision
        data['branch'] = branch
        data['project'] = self.conf.project
        data['environment'] = self.conf.environment
        return data

    def upload_json(self, filename, branch, revision):
        # Import perf module from --perf directory
        sys.path.insert(0, self.conf.perf)

        import perf

        suite = perf.BenchmarkSuite.load(filename)
        data = [self.encode_benchmark(bench, branch, revision) for bench in suite]
        data = dict(json=json.dumps(data))

        url = self.conf.url
        if not url.endswith('/'):
            url += '/'
        url += 'result/add/json/'
        self.logger.error("Upload %s benchmarks to %s" % (len(suite), url))

        try:
            response = urlopen(data=urlencode(data).encode('utf-8'), url=url)
            self.logger.error('Response: "%s"' % response.read().decode('utf-8'))
            response.close()
            return True
        except HTTPError as err:
            self.logger.error("HTTP Error: %s" % err)
            errmsg = err.read().decode('utf8')
            self.logger.error(errmsg)
            err.close()
            return False

    def error(self, msg):
        self.logger.error("ERROR: %s" % msg)
        self.errors.append(msg)

    def benchmark(self, is_branch, revision):
        if is_branch:
            branch = revision
        else:
            branch = branch or DEFAULT_BRANCH

        bench = BenchmarkPython(self.conf, node, branch)
        filename = bench.filename
        if os.path.exists(filename):
            self.skipped.append(filename)
            return
        bench.main(node)

        if self.options:
            cmd.extend(self.conf.options)
        if self.conf.debug:
            cmd.append('--debug')

        exitcode = self.run_nocheck(cmd)
        if exitcode:
            self.failed.append(filename)
            return

        if self.conf.upload:
            filename2 = os.path.join(self.conf.uploaded_json_dir,
                                     os.path.basename(filename))
            if os.path.exists(filename2):
                self.error("cannot upload, %s file ready exists!" % filename2)
            else:
                # FIXME: pass the full node, not only the short node
                # CodeSpeed needs to be modified to only displays short nodes
                uploaded = self.upload_json(filename, branch, short_node)

                if uploaded:
                    os.move(filename, filename2)
                    filename = filename2
        else:
            uploaded = False

        if uploaded:
            self.uploaded.append(filename)
        else:
            self.outputs.append(filename)

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('config_filename',
                            help='Configuration filename')
        return parser.parse_args()

    def main(self):
        args = self.parse_args()
        self.conf = parse_config(args.config_filename)

        if self.conf.debug and self.conf.upload:
            self.logger.error("ERROR: debug mode is incompatible with upload")
            sys.exit(1)

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

            for error in self.errors:
                self.logger.error("ERROR: %s" % error)


def cmd_compile(options):
    conf = parse_config(options.config_filename)
    revision = options.revision
    BenchmarkPython(conf, revision).main()
