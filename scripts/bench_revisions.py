#!/usr/bin/env python3
import argparse
import configparser
import datetime
import errno
import json
import os.path
import shutil
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


class Benchmark(object):
    def __init__(self):
        bench_dir = os.path.realpath(os.path.dirname(__file__))
        self.bench_cpython = os.path.join(bench_dir, 'bench_cpython.py')
        self.outputs = []
        self.skipped = []
        self.uploaded = []
        self.failed = []

    def get_revision_info(self, revision):
        cmd = ['hg', 'log', '--template', '{node}|{branch}|{date|isodate}', '-r', revision]
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                cwd=self.src,
                                universal_newlines=True)
        stdout = proc.communicate()[0]
        if proc.returncode:
            sys.exit(proc.returncode)
        node, branch, stdout = stdout.split('|')
        date = datetime.datetime.strptime(stdout[:16], '%Y-%m-%d %H:%M')
        return (node, branch, date)

    def run_cmd(self, cmd, **kw):
        check = kw.pop('check', True)
        print('+ %s' % ' '.join(cmd))
        proc = subprocess.Popen(cmd, **kw)
        exitcode = proc.wait()
        if check and exitcode:
            sys.exit(exitcode)
        return exitcode

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

    def benchmark(self, revision, name=None):
        node, branch, date = self.get_revision_info(revision)
        short_node = node[:12]
        date = date.strftime('%Y-%m-%d_%H-%M')
        filename = '%s-%s-%s' % (date, branch, short_node)
        if name:
            filename += '-%s' % name
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

        exitcode = self.run_cmd(cmd, check=False)
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
        self.run_cmd(('sudo', 'python3', '-m', 'perf', 'system', 'tune'),
                     cwd=self.perf)
        if self.update:
            self.run_cmd(('hg', 'pull'), cwd=self.src)

        try:
            for revision, name in self.revisions:
                self.benchmark(revision, name)

            for branch in self.branches:
                self.benchmark(branch)
        finally:
            for filename in self.skipped:
                print("Skipped: %s" % filename)

            for filename in self.outputs:
                print("Tested: %s" % filename)

            for filename in self.uploaded:
                print("Tested and uploaded: %s" % filename)

            for filename in self.failed:
                print("FAILED: %s" % filename)


if __name__ == "__main__":
    Benchmark().main()
