#!/usr/bin/env python

import sys
import os
import re
import subprocess
from warnings import warn
from parser import get_parser, analyze

# Monkey-patch Py2 subprocess
if not hasattr(subprocess, 'DEVNULL'):
    subprocess.DEVNULL = -3

if not hasattr(subprocess, 'run'):
    # Reimplement minimal functionality for usage in this file
    def _run(args, stdout=None, stderr=None):
        from collections import namedtuple
        result = namedtuple('CompletedProcess', 'stdout stderr returncode')

        devnull = None
        if subprocess.DEVNULL in (stdout, stderr):
            devnull = open(os.devnull, 'r+')
            if stdout == subprocess.DEVNULL:
                stdout = devnull
            if stderr == subprocess.DEVNULL:
                stderr = devnull

        proc = subprocess.Popen(args, stdout=stdout, stderr=stderr)
        stdout, stderr = proc.communicate()
        res = result(stdout, stderr, proc.returncode)

        if devnull is not None:
            devnull.close()

        return res
    subprocess.run = _run

def main():
    opts = get_parser().parse_args()
    ret = subprocess.run(['docker', 'version', '--format', "{{.Server.Version}}"],
                         stdout=subprocess.PIPE)
    docker_version = ret.stdout.decode('ascii').strip()
    command = ['docker', 'run', '--rm', '-it', '-e',
               'DOCKER_VERSION_8395080871=%s' % docker_version]
    main_args = []
    if opts.bids_directory:
        command.extend(['-v', ':'.join((opts.bids_directory, opts.bids_directory))])
        main_args.append('/data')
    if opts.output_directory:
        command.extend(['-v', ':'.join((opts.output_directory, opts.output_directory))])
        main_args.append('/out')
    command.append('test')
    command.extend(sys.argv[1:])
    print("RUNNING: " + ' '.join(command))
    ret = subprocess.run(command)
    if ret.returncode:
        print("fPETPrep: Please report errors")
    return ret.returncode

main()