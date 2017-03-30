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


class Repository(object):
    def __init__(self, app, path):
        self.path = path
        self.logger = app.logger

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

    def checkout(self, revision, fetch):
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
        log_format = '%(asctime)-15s: %(message)s'
        logging.basicConfig(format=log_format)
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


class BenchmarkPython(Application):
    def __init__(self):
        super().__init__()
        self.args = self.parse_args()
        self.python = None

        if self.args.log:
            handler = logging.FileHandler(self.args.log)
            formatter = logging.Formatter(log_format)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def prepare_code(self):
        args = self.args

        self.repository = Repository(self, os.getcwd())

        self.logger.error('')
        text = "Benchmark CPython revision %s" % args.revision
        self.logger.error(text)
        self.logger.error("=" * len(text))
        self.logger.error('')

        if args.pull:
            self.repository.fetch()
        self.repository.checkout(args.revision)

        if args.patch:
            self.logger.error('Apply patch %s' % args.patch)
            self.run('patch', '-p1', stdin_filename=args.patch)

        full_revision = self.repository.get_revision()
        self.logger.error("Revision: %s" % full_revision)

    def compile(self):
        args = self.args

        self.run_nocheck('make', 'distclean')

        config_args = []
        if args.debug:
            config_args.append('--with-pydebug')
        elif args.lto:
            config_args.append('--with-lto')
        if args.prefix:
            config_args.extend(('--prefix', args.prefix))
        self.run('./configure', *config_args)

        self.run_nocheck('make', 'clean')

        if args.pgo:
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
        args = self.args
        prefix = args.prefix

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
        args = self.args

        # Create venv
        cmd = [self.python, '-u', '-m', 'performance', 'venv', 'recreate']
        if args.venv:
            cmd.extend(('--venv', args.venv))
        self.run(*cmd)

        cmd = [self.python, '-u',
               '-m', 'performance',
               'run', '--verbose']
        if args.output:
            cmd.extend(('--output', args.output))
        if args.venv:
            cmd.extend(('--venv', args.venv))
        if args.debug:
            cmd.append('--debug-single-value')
        elif args.rigorous:
            cmd.append('--rigorous')
        self.run(*cmd)

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-o', '--output', metavar='JSON_FILENAME',
                            help='write results encoded to JSON into JSON_FILENAME')
        parser.add_argument('--log', metavar='FILENAME',
                            help='Write logs into FILENAME log file')
        parser.add_argument('--pgo', action='store_true',
                            help='Enable Profile Guided Optimization (PGO)')
        parser.add_argument('--lto', action='store_true',
                            help='Enable Link Time Optimization (LTO)')
        parser.add_argument('--src',
                            help='Directory of Python source code',
                            required=True)
        parser.add_argument('--venv',
                            help="Directory of virtual environmented used "
                                 "to run performance benchmarks. Create it "
                                 "if it doesn't exist")
        parser.add_argument('--prefix',
                            help="Directory where Python is installed: "
                                 "--prefix parameter of the ./configure script.")
        parser.add_argument('--debug', action="store_true",
                            help="Enable the debug mode")
        parser.add_argument('--rigorous', action="store_true",
                            help="Enable the rigorous mode: "
                                 "run more benchmark values")
        parser.add_argument('--pull', action="store_true",
                            help='Run git fetch to fetch new commits')
        parser.add_argument('--patch',
                            help='Apply a patch on top on revision '
                                 'before compiling Python')
        parser.add_argument('revision',
                            help='Python benchmarked revision')
        args = parser.parse_args()

        if not args.prefix:
            # FIXME
            print("ERROR: running benchmark without installation "
                  "is currently broken")
            sys.exit(1)

        for attr in ('src', 'prefix', 'output'):
            # Since we use os.chdir(), all paths must be absolute
            path = getattr(args, attr)
            if not path:
                continue
            path = os.path.expanduser(path)
            path = os.path.realpath(path)
            setattr(args, attr, path)

        if args.debug:
            args.pgo = False
            args.lto = False

        if args.venv:
            args.venv = os.path.realpath(args.venv)

        if args.output and os.path.exists(args.output):
            print("ERROR: %s already exists" % args.output)
            sys.exit(1)

        return args

    def main(self):
        self.start = time.monotonic()

        self.logger.error("Run benchmarks")
        self.logger.error('')

        if self.args.log:
            self.logger.error("Write logs into %s" % self.args.log)

        self.logger.error("Move to %s" % self.args.src)
        os.chdir(self.args.src)

        self.prepare_code()
        self.compile()
        self.install()
        self.run_benchmark()

        dt = time.monotonic() - self.start
        dt = datetime.timedelta(seconds=dt)
        self.logger.error("Benchmark completed in %s" % dt)


class Benchmark(Application):
    def __init__(self):
        super().__init__()
        bench_dir = os.path.realpath(os.path.dirname(__file__))
        self.bench_cpython = os.path.join(bench_dir, 'bench_cpython.py')
        self.outputs = []
        self.skipped = []
        self.uploaded = []
        self.failed = []

    def encode_benchmark(self, bench, branch, revision):
        data = {}
        data['benchmark'] = bench.get_name()
        data['result_value'] = bench.mean()

        values = bench.get_values()
        data['min'] = min(values)
        data['max'] = max(values)
        data['std_dev'] = bench.stdev()

        data['executable'] = self.executable
        data['commitid'] = revision
        data['branch'] = branch
        data['project'] = self.project
        data['environment'] = self.environment
        return data

    def upload_json(self, filename, branch, revision):
        import perf

        suite = perf.BenchmarkSuite.load(filename)
        data = [self.encode_benchmark(bench, branch, revision) for bench in suite]
        data = dict(json=json.dumps(data))

        url = self.url
        if not url.endswith('/'):
            url += '/'
        url += 'result/add/json/'
        print("Upload %s benchmarks to %s" % (len(suite), url))

        try:
            response = urlopen(data=urlencode(data).encode('utf-8'), url=url)
            print('Response: "%s"' % response.read().decode('utf-8'))
            response.close()
            return True
        except HTTPError as err:
            print("HTTP Error: %s" % err)
            errmsg = err.read().decode('utf8')
            print(errmsg)
            err.close()
            return False

    def benchmark(self, is_branch, revision):
        if is_branch:
            branch = revision
        else:
            branch = branch or DEFAULT_BRANCH

        node, date = self.repository.get_revision_info(revision)
        short_node = node[:12]
        date = date.strftime('%Y-%m-%d_%H-%M')
        filename = '%s-%s-%s' % (date, branch, short_node)
        filename = os.path.join(self.directory, filename + ".json")

        if os.path.exists(filename):
            self.skipped.append(filename)
            return

        try:
            shutil.rmtree(self.prefix)
        except FileNotFoundError:
            pass

        cmd = ['python3', self.bench_cpython,
               '--src', self.src,
               '--log', self.log,
               '--output', filename,
               '--venv', self.venv,
               '--prefix', self.prefix,
               node]
        if self.options:
            cmd.extend(self.options)
        if self.debug:
            cmd.append('--debug')

        exitcode = self.run_nocheck(cmd)
        if exitcode:
            self.failed.append(filename)
            return

        if self.upload:
            # FIXME: pass the full node, not only the short node
            # CodeSpeed needs to be modified to only displays short nodes
            uploaded = self.upload_json(filename, branch, short_node)
        else:
            uploaded = False

        if uploaded:
            self.uploaded.append(filename)
        else:
            self.outputs.append(filename)

    def safe_makedirs(self, directory):
        try:
            os.makedirs(directory)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('config_filename',
                            help='Configuration filename')
        return parser.parse_args()

    def parse_config(self, filename):
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

        self.directory = os.path.expanduser(getstr('config', 'bench_root'))
        self.src = os.path.expanduser(getstr('config', 'cpython_dir'))
        self.perf = os.path.expanduser(getstr('config', 'perf_dir'))
        self.prefix = os.path.join(self.directory, 'prefix')
        self.venv = os.path.join(self.directory, 'venv')
        self.log = os.path.join(self.directory, 'bench.log')
        self.options = getstr('config', 'options').split()
        self.branches = getstr('config', 'branches').split()
        self.update = config.getboolean('update', True)
        self.debug = config.getboolean('debug', False)
        self.upload = config.getboolean('upload', False)

        if self.upload:
            UPLOAD_OPTIONS = ('url', 'environment', 'executable', 'project')

            self.url = getstr('upload', 'url', default='')
            self.executable = getstr('upload', 'executable', default='')
            self.project = getstr('upload', 'project', default='')
            self.environment = getstr('upload', 'environment', default='')

            if any(not getattr(self, attr) for attr in UPLOAD_OPTIONS):
                print("ERROR: Upload requires to set the following "
                      "configuration option in the the [upload] section "
                      "of %s:"
                      % filename)
                for attr in UPLOAD_OPTIONS:
                    text = "- %s" % attr
                    if not getattr(self, attr):
                        text += " (not set)"
                    print(text)
                sys.exit(1)

        self.revisions = []
        try:
            revisions = cfgobj.items('revisions')
        except configparser.NoSectionError:
            pass
        else:
            for revision, name in revisions:
                self.revisions.append((revision, name))

    def main(self):
        args = self.parse_args()
        self.parse_config(args.config_filename)

        # Import perf module from --perf directory
        sys.path.insert(0, self.perf)

        self.safe_makedirs(self.directory)
        self.run('sudo', 'python3', '-m', 'perf', 'system', 'tune',
                 cwd=self.perf)

        self.repository = Repository(self, self.src)
        if self.update:
            self.repository.fetch()

        try:
            for revision, branch in self.revisions:
                self.benchmark(False, revision)

            for branch in self.branches:
                self.benchmark(True, branch)
        finally:
            for filename in self.skipped:
                print("Skipped: %s" % filename)

            for filename in self.outputs:
                print("Tested: %s" % filename)

            for filename in self.uploaded:
                print("Tested and uploaded: %s" % filename)

            for filename in self.failed:
                print("FAILED: %s" % filename)
