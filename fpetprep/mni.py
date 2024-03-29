import os, uuid
import shutil, json
import tempfile
import subprocess
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from os.path import join, isdir, basename, splitext, dirname
from os import mkdir
from glob import glob
from pathlib import Path


class Mni:
    def __init__(self, opts):
        self.resolution = opts.resolution
        self.input_dir = str(opts.bids_directory)
        if opts.output_directory:
             self.output_dir = opts.output_directory
        else:
            self.output_dir = join(str(opts.bids_directory),'derivatives')
        if not isdir(self.output_dir): os.makedirs(self.output_dir)
        if opts.mni_include_sub_directory:
            self.input_nii = list(Path(self.input_dir).glob('sub*/*/*.nii.gz'))
            self.input_nii = [str(file) for file in self.input_nii]
        else:
            self.input_nii = list(glob(join(self.input_dir, '*.nii.gz')))
        #TODO: figure out whether we need subdirectory file as well
        # and how to save those
        # example for input_root: static_suv_niis or dyn_suv_niis
        self.gaussian_filter = tuple(opts.gaussian_filter)
        self.normalized_nii, self.smoothed_nii, self.intensity_norm_nii = self.generate_file_list()
        self.save_intermediate_files = opts.save_intermediate_files

    def generate_file_list(self):
        if not isdir(join(self.output_dir,'mni_normalize')):
            mkdir(join(self.output_dir, 'mni_normalize'))
        if not isdir(join(self.output_dir,'mni_smoothed')):
            mkdir(join(self.output_dir,'mni_smoothed'))
        if not isdir(join(self.output_dir, 'mni_intensity')):
            mkdir(join(self.output_dir, 'mni_intensity'))
        normalized_nii = []
        smoothed_nii = []
        intensity_norm_nii = []
        for file in self.input_nii:
            file_dir, file_name = os.path.split(file)
            splitext(file_name)[0].rstrip('.nii') + '_mni_normalize.nii' + splitext(file_name)[1]
            file_com = file_dir.split(os.sep)
            root_com = str(self.input_dir).split(os.sep)
            # new_com = list(set(file_com).difference(root_com))
            new_com = [i for i in file_com if i not in root_com]
            normalized = join(self.input_dir,'derivatives','mni_normalize',*new_com, splitext(file_name)[0].rstrip('.nii') + '_mni_normalize.nii' + splitext(file_name)[1])
            smoothed = join(self.input_dir, 'derivatives', 'mni_smoothed', *new_com,splitext(file_name)[0].rstrip('.nii') + '_mni_smoothed.nii' + splitext(file_name)[1])
            intensity = join(self.input_dir, 'derivatives', 'mni_intensity', *new_com,splitext(file_name)[0].rstrip('.nii') + '_mni_intensity.nii' + splitext(file_name)[1])
            normalized_nii.append(normalized)
            smoothed_nii.append(smoothed)
            intensity_norm_nii.append(intensity)
        if not len(normalized_nii) == len(smoothed_nii) or not len(normalized_nii) == len(intensity_norm_nii):
            raise ValueError('Dimension mismatch')
        return normalized_nii, smoothed_nii, intensity_norm_nii


    def run(self):
        # step 1: normalization to mni space
        self.normalization_2_common_space()
        # step 2: smoothing using gaussian filter = (3, 3, 3)
        self.smooth_gaussian()
        # step 3: intensity normalization
        self.normalization_intensity()
        if not self.save_intermediate_files:
            print('delete intermediate files')
            norm_dir = join(self.output_dir, 'mni_normalize')
            smooth_dir = join(self.output_dir, 'mni_smoothed')
            shutil.rmtree(norm_dir)
            shutil.rmtree(smooth_dir)

    def get_mni152_nii_file(self,input_file_name):
        base_file_name, _ = splitext(basename(input_file_name))
        json_data = json.load(open(join(dirname(input_file_name),base_file_name.rstrip('.nii') +'.json')))
        if 'Modality' in json_data:
            modality = json_data['Modality']
            if modality == 'PET' or modality == 'PT':
                data_type = 'pet'
            else:
                data_type = 't1w'
        elif 'suvbw_factor' in json_data:
            data_type = 'pet'
        else:
            raise ValueError('cannot determine which template to use') # TODO: add parser so that user can specify their own
        return os.path.join(os.path.dirname(__file__), 'template',
                            'mni152_' + data_type + '_' + self.resolution + '.nii.gz')


    def normalization_2_common_space(self):
        print('normalization')
        for (input_nii_file,output_nii_file) in zip(self.input_nii, self.normalized_nii):
            print('run %s' % input_nii_file)
            print('generate %s' % output_nii_file)
            if os.path.exists(output_nii_file): continue
            dir_name = os.path.dirname(output_nii_file)
            if not os.path.exists(dir_name): os.makedirs(dir_name)
            mni_nii_file = self.get_mni152_nii_file(input_nii_file)
            nib_img = nib.load(input_nii_file)
            if len(nib_img.shape) > 3:
                nib_3d_imgs = nib.four_to_three(nib_img)
            else:
                nib_3d_imgs = [nib_img]
            dyn_3d_nib_files = []
            dyn_3d_nib_in_root = tempfile.mkdtemp()
            for nib_3d_img in nib_3d_imgs:
                nib_3d_img_file = os.path.join(dyn_3d_nib_in_root, uuid.uuid4().__str__() + '.nii.gz')
                nib_3d_img.to_filename(nib_3d_img_file)
                dyn_3d_nib_files.append(nib_3d_img_file)
            dyn_3d_nib_out_root = tempfile.mkdtemp()
            dyn_3d_nib_out_files = []
            for dyn_3d_nib_file in dyn_3d_nib_files:
                dyn_3d_nib_out_file = os.path.join(dyn_3d_nib_out_root, uuid.uuid4().__str__() + '.nii.gz')
                devnull = open(os.devnull, 'w')
                subprocess.call(['flirt',
                                 '-in', dyn_3d_nib_file,
                                 '-out', dyn_3d_nib_out_file,
                                 '-ref', mni_nii_file,
                                 '-bins', '256',
                                 '-dof', '12'],stdout=devnull, stderr=subprocess.STDOUT)
                dyn_3d_nib_out_files.append(dyn_3d_nib_out_file)
            nib_3d_imgs = []
            for dyn_3d_nib_out_file in dyn_3d_nib_out_files:
                nib_3d_imgs.append(nib.load(dyn_3d_nib_out_file))
            if len(nib_3d_imgs) > 1:
                nib_4d_img = nib.concat_images(nib_3d_imgs)
                nib_4d_img.to_filename(output_nii_file)
            else:
                nib_3d_imgs[0].to_filename(output_nii_file)
            if os.path.isdir(dyn_3d_nib_in_root): shutil.rmtree(dyn_3d_nib_in_root)
            if os.path.isdir(dyn_3d_nib_out_root): shutil.rmtree(dyn_3d_nib_out_root)
        return

    def smooth_gaussian(self):
        gaussian_filter = self.gaussian_filter
        for (input_nii_file, output_nii_file) in zip(self.normalized_nii,self.smoothed_nii):
            print('run gaussian smooth %s' % (input_nii_file))
            print('generate %s' % output_nii_file)
            if os.path.exists(output_nii_file): continue
            dir_name = os.path.dirname(output_nii_file)
            if not os.path.exists(dir_name): os.makedirs(dir_name)
            nib_img = nib.load(input_nii_file)
            if len(nib_img.shape) > 3:
                nib_3d_imgs = nib.four_to_three(nib_img)
            else:
                nib_3d_imgs = [nib_img]
            dyn_3d_nib_files = []
            dyn_3d_nib_in_root = tempfile.mkdtemp()
            for nib_3d_img in nib_3d_imgs:
                nib_3d_img_file = os.path.join(dyn_3d_nib_in_root, uuid.uuid4().__str__() + '.nii.gz')
                nib_3d_img.to_filename(nib_3d_img_file)
                dyn_3d_nib_files.append(nib_3d_img_file)
            dyn_3d_nib_out_root = tempfile.mkdtemp()
            dyn_3d_nib_out_files = []
            for dyn_3d_nib_file in dyn_3d_nib_files:
                dyn_3d_nib_out_file = os.path.join(dyn_3d_nib_out_root, uuid.uuid4().__str__() + '.nii.gz')
                sitk_image_0 = sitk.ReadImage(dyn_3d_nib_file)
                sitk_image_1 = sitk.SmoothingRecursiveGaussian(sitk_image_0, gaussian_filter)
                sitk.WriteImage(sitk_image_1, dyn_3d_nib_out_file)
                dyn_3d_nib_out_files.append(dyn_3d_nib_out_file)
            nib_3d_imgs = []
            for dyn_3d_nib_out_file in dyn_3d_nib_out_files:
                nib_3d_imgs.append(nib.load(dyn_3d_nib_out_file))
            if len(nib_3d_imgs) > 1:
                nib_4d_img = nib.concat_images(nib_3d_imgs)
                nib_4d_img.to_filename(output_nii_file)
            else:
                nib_3d_imgs[0].to_filename(output_nii_file)
            if isdir(dyn_3d_nib_in_root): shutil.rmtree(dyn_3d_nib_in_root)
            if isdir(dyn_3d_nib_out_root): shutil.rmtree(dyn_3d_nib_out_root)
        return

    def normalization_intensity(self):
        for (input_nii_file, output_nii_file) in zip(self.smoothed_nii, self.intensity_norm_nii):
            print('run intensity normalization %s' % input_nii_file)
            print('generate %s' % output_nii_file)
            if os.path.exists(output_nii_file): continue
            dir_name = os.path.dirname(output_nii_file)
            if not os.path.exists(dir_name): os.makedirs(dir_name)
            nib_img = nib.load(input_nii_file)
            if len(nib_img.shape) > 3:
                nib_3d_imgs = nib.four_to_three(nib_img)
            else:
                nib_3d_imgs = [nib_img]
            dyn_3d_nib_files = []
            dyn_3d_nib_in_root = tempfile.mkdtemp()
            for nib_3d_img in nib_3d_imgs:
                nib_3d_img_file = os.path.join(dyn_3d_nib_in_root, uuid.uuid4().__str__() + '.nii.gz')
                nib_3d_img.to_filename(nib_3d_img_file)
                dyn_3d_nib_files.append(nib_3d_img_file)
            dyn_3d_nib_out_root = tempfile.mkdtemp()
            dyn_3d_nib_out_files = []
            for dyn_3d_nib_file in dyn_3d_nib_files:
                dyn_3d_nib_out_file = os.path.join(dyn_3d_nib_out_root, uuid.uuid4().__str__() + '.nii.gz')
                nib_3d_img = nib.load(dyn_3d_nib_file)
                np_3d_img = nib_3d_img.get_data()
                np_3d_img_norm = np_3d_img / np.mean(np_3d_img)
                nib_3d_img_norm = nib.Nifti1Image(np_3d_img_norm, nib_3d_img.affine)
                nib_3d_img_norm.to_filename(dyn_3d_nib_out_file)
                dyn_3d_nib_out_files.append(dyn_3d_nib_out_file)
            nib_3d_imgs = []
            for dyn_3d_nib_out_file in dyn_3d_nib_out_files:
                nib_3d_imgs.append(nib.load(dyn_3d_nib_out_file))
            if len(nib_3d_imgs) > 1:
                nib_4d_img = nib.concat_images(nib_3d_imgs)
                nib_4d_img.to_filename(output_nii_file)
            else:
                nib_3d_imgs[0].to_filename(output_nii_file)
            if os.path.isdir(dyn_3d_nib_in_root): shutil.rmtree(dyn_3d_nib_in_root)
            if os.path.isdir(dyn_3d_nib_out_root): shutil.rmtree(dyn_3d_nib_out_root)
        return

    def group_normalization(self):
        print('run group normalization')
        np_imgs_mean = []
        affines = []
        for input_nii_file in self.intensity_norm_nii:
            nib_img = nib.load(input_nii_file)
            np_img = nib_img.get_data()
            if len(np_img.shape) == 4:
                np_img_mean = np.mean(np_img, axis=-1)
            else:
                np_img_mean = np_img
            np_imgs_mean.append(np_img_mean)
            affines.append(nib_img.affine)
        np_img_group = np.mean(np.array(np_imgs_mean), axis=0)
        nib_img = nib.Nifti1Image(np_img_group, affines[0])
        nib_img.to_filename(join(self.input_dir, 'dyn_group.nii'))
        return


    def diff_paired_nii(self,paired_nii_file_0, paired_nii_file_1, output_nii_file):
        print('run difference paried nii %s - %s' % (basename(paired_nii_file_0),
                                                     basename(paired_nii_file_1)))
        nib_img_0 = nib.load(paired_nii_file_0)
        np_img_0 = nib_img_0.get_data()
        nib_img_1 = nib.load(paired_nii_file_1)
        np_img_1 = nib_img_1.get_data()
        np_img = np_img_0 - np_img_1
        if np.mean(np_img_1) - np.mean(np_img_0) > 0.0: np_img = np_img_1 - np_img_0
        nib_img = nib.Nifti1Image(np_img, nib_img_0.affine)
        nib_img.to_filename(output_nii_file)
        return

