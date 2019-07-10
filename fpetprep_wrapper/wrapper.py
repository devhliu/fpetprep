#!/usr/bin/env python3

import sys
import os
import re
import subprocess
from warnings import warn
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter

MISSING = """
Image '{}' is missing
Would you like to download? [Y/n] """
PKG_PATH = '/usr/local/miniconda/lib/python3.7/site-packages'

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

def getParser():
    parser = ArgumentParser(description='fPETPrep: PET pre-processing workflow',
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('bids_directory',action = 'store', type=str,
                        help= 'root folder for your BIDS format data')
    p_wrapper = parser.add_argument_group('Options for wrapper (only included those need to be mapped into the container')
    p_wrapper.add_argument('--output_directory', required = False, action='store', default=[],type=str,
                        help='directory to store output')
    p_wrapper.add_argument('--dicom_directory', required='--convert2bids' in sys.argv or '--generate_excel_file' in sys.argv,
                                   action='store', type=str, help='root folder for dicom data')
    p_wrapper.add_argument('--excel_file_path',action='store', required='--convert2bids' in sys.argv, type=str)
    p_wrapper.add_argument('--ica_file_list',required= '--ica' in sys.argv and '--ica_file_directory' not in sys.argv,action='store',type=str)
    return parser

def main():
    parser = getParser()
    opts, unknown_args = parser.parse_known_args()
    ret = subprocess.run(['docker', 'version', '--format', "{{.Server.Version}}"],
                         stdout=subprocess.PIPE)
    docker_version = ret.stdout.decode('ascii').strip()
    command = ['docker', 'run', '--rm', '-it', '-e',
               'DOCKER_VERSION_8395080871=%s' % docker_version]
    if opts.bids_directory:
        command.extend(['-v', ':'.join((opts.bids_directory, opts.bids_directory))])
    if opts.output_directory:
        command.extend(['-v', ':'.join((opts.output_directory, opts.output_directory))])
    if opts.dicom_directory:
        command.extend(['-v', ':'.join((opts.dicom_directory, opts.dicom_directory))])
    if opts.ica_file_list:
        file_dir = os.path.dirname(opts.ica_file_list)
        command.extend(['-v', ':'.join((file_dir, file_dir))])
    if opts.excel_file_path:
        file_dir = os.path.dirname(opts.excel_file_path)
        command.extend(['-v', ':'.join((file_dir, file_dir))])
    command.append('test')
    command.extend(sys.argv[1:])
    print("RUNNING: " + ' '.join(command))
    ret = subprocess.run(command)
    if ret.returncode:
        print("fPETPrep: Please report errors")
    return ret.returncode

#if __name__ == '__main__':
#    sys.exit(main())