#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(name='fpetprep_docker',
      version='0.0.0',
      description='preprocessing tool for fmri/pet data',
      url='https://github.com/devhliu/fpetprep', 
      entry_points = {'console_scripts':['fpetprep-docker = fpetprep_wrapper:main']},
      zip_safe=False)
