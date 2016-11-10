#!/usr/bin/env python3
import argparse
import configparser
import datetime
import errno
import os.path
import shutil
import subprocess
import sys


REVISIONS = (
    # OLD -> NEW

    # Before the sprint, Sep 04 2016
    ("before-sprint", "8e9d3a5d47d5"),

    # After: Compact dict
    ("compact-dict", "0bd618fe0639"),
    # After: Rework CALL_FUNCTION opcodes
    ("rework-call-opcode", "a77756e480c2"),
    # After: all FASTCALL changes
    ("fastcall", "97a68adbe826"),

    ("sept15", "b6ca2d734f8e"),
    ("sept20", "0480b540a451"),
    ("sept25", "1c5e0dbcb2a0"),

    ("oct1", "f12f8a5960f0"),
    ("oct10", "678fe178da0d"),
    ("oct20", "1ce50f7027c1"),
)


class Benchmark(object):
    def __init__(self):
        bench_dir = os.path.realpath(os.path.dirname(__file__))
        self.bench_cpython = os.path.join(bench_dir, 'bench_cpython.py')
        self.outputs = []
        self.skipped = []

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
        print('+ %s' % ' '.join(cmd))
        proc = subprocess.Popen(cmd, **kw)
        exitcode = proc.wait()
        if exitcode:
            sys.exit(exitcode)

    def benchmark(self, revision, name=None):
        node, branch, date = self.get_revision_info(revision)
        date = date.strftime('%Y-%m-%d_%H-%M')
        filename = '%s-%s-%s' % (date, branch, node[:12])
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
               revision]
        if self.options:
            cmd.append(self.options)
        if self.debug:
            cmd.append('--debug')
        self.run_cmd(cmd)

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

        def get(section, key):
            return section[key].strip()

        self.directory = os.path.expanduser(get(config, 'bench_root'))
        self.src = os.path.expanduser(get(config, 'cpython_dir'))
        self.perf = os.path.expanduser(get(config, 'perf_dir'))
        self.prefix = os.path.join(self.directory, 'prefix')
        self.venv = os.path.join(self.directory, 'venv')
        self.log = os.path.join(self.directory, 'bench.log')
        self.options = get(config, 'options')
        self.branches = get(config, 'branches').split()
        self.update = config.getboolean('update', True)
        self.debug = config.getboolean('debug', False)

        self.revisions = []
        section = cfgobj['revisions']
        for revision, name in cfgobj.items('revisions'):
            self.revisions.append((revision, name))

    def main(self):
        args = self.parse_args()
        self.parse_config(args.config_filename)
        self.safe_makedirs(self.directory)
        self.run_cmd(('sudo', 'python3', '-m', 'perf', 'system', 'tune'),
                     cwd=self.perf)
        if self.update:
            self.run_cmd(('hg', 'pull'), cwd=self.src)

        try:
            for branch in self.branches:
                self.benchmark(branch)

            for revision, name in self.revisions:
                self.benchmark(revision, name)
        finally:
            for filename in self.skipped:
                print("Skipped: %s" % filename)

            for filename in self.outputs:
                print("Tested: %s" % filename)


if __name__ == "__main__":
    Benchmark().main()
