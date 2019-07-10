#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(name='fpetprepDocker',
      version='0.0',
      description='preprocessing tool for fmri/pet data',
      url='https://github.com/devhliu/fpetprep', 
      py_modules=['wrapper'],
      entry_points = {'console_scripts':['fpetprepDocker = wrapper:main']},
      zip_safe=False)
