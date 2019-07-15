import os
import numpy as np
import nibabel as nib
from os.path import abspath, join, isdir
from glob import glob
from nilearn.image import concat_imgs
import logging
def Noise_rest(root_dir):
    rest_list = glob(join(root_dir, 'sub*/staticPET',"*rest*.nii.gz"))
    noise_list = glob(join(root_dir, 'sub*/staticPET',"*noise*.nii.gz"))
    eg = nib.load(rest_list[0])
    for (rest_file,noise_file) in zip(rest_list,noise_list):
        rest = nib.load(rest_file).get_data()
        noise = nib.load(noise_file).get_data()
        rel_val = noise - rest
        out = nib.Nifti1Image(rel_val, eg.affine)
        rel_file = rest_file.replace('rest','rel')
        out.to_filename(rel_file)
    return