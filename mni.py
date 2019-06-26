import os
import uuid
import shutil
import tempfile
import subprocess
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from os.path import join, isdir, basename
from os import mkdir
from glob import glob


class Mni:
    def __init__(self, opts):
        # TODO: add related parameters to parser.py
        self.type = opts.type
        self.resolution = opts.resolution
        self.root_dir = opts.bids_directory
        self.input_nii = glob(join(self.root_dir, '*.nii.gz'))
        #TODO: figure out whether we need subdirectory file as well
        # and how to save those
        # example for input_root: static_suv_niis or dyn_suv_niis
        self.mkdir()
        self.normalized_nii = [join(self.root_dir,'mni_normalize', basename(file)) for file in self.input_nii]
        self.smoothed_nii = [join(self.root_dir,'mni_gaussian', basename(file)) for file in self.normalized_nii]
        self.intensity_norm_nii = [join(self.root_dir,'mni_intensity_norm', basename(file)) for file in self.smoothed_nii]
        self.gaussian_filter = tuple(opts.gaussian_filter)
        '''if opts.save_intermediate_files:
                    self.save_intermediate_files = opts.save_intermediate_files
                    #uncomment this when its actually implemented (rm the related directory)
                else: 
                    self.save_intermediate_files = True'''

    def mkdir(self):
        if not isdir(join(self.root_dir,'mni_normalize')):
            mkdir(join(self.root_dir, 'mni_normalize'))
        if not isdir(join(self.root_dir,'mni_gaussian')):
            mkdir(join(self.root_dir,'mni_gaussian'))
        if not isdir(join(self.root_dir, 'mni_intensity_norm')):
            mkdir(join(self.root_dir, 'mni_intensity_norm'))


    def run(self):
            print(str(self.input_nii))
            print(str(self.normalized_nii))
            print(str(self.smoothed_nii))
            print(str(self.intensity_norm_nii))
            
            # TODO: figure out how get_mni152_nii_file works
            # step 1: normalization to mni space
            self.normalization_2_common_space(self.get_mni152_nii_file())
            # step 2: smoothing using gaussian filter = (3, 3, 3)
            self.smooth_gaussian()
            # step 3: intensity normalization
            self.normalization_intensity()
            # step 4： difference paired
            # TODO: add the 4th step

    def get_mni152_nii_file(self):
        return os.path.join(os.path.dirname(__file__), 'template',
                            'mni152_' + self.type + '_' + self.resolution + '.nii.gz')


    def normalization_2_common_space(self, mni_nii_file):
        for (input_nii_file,output_nii_file) in zip(self.input_nii, self.normalized_nii):
            nib_img = nib.load(input_nii_file)
            print('run %s' % (input_nii_file))
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
                subprocess.call(['flirt',
                                 '-in', dyn_3d_nib_file,
                                 '-out', dyn_3d_nib_out_file,
                                 '-ref', mni_nii_file,
                                 '-bins', '256',
                                 '-dof', '12'])
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
        """
        :param input_nii_file:
        :param output_nii_file:
        :param gaussian_filter:
        :return:
        """
        gaussian_filter = self.gaussian_filter
        for (input_nii_file, output_nii_file) in zip(self.normalized_nii,self.smoothed_nii):
            print('run gaussian smooth %s' % (input_nii_file))
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
            if os.path.isdir(dyn_3d_nib_in_root): shutil.rmtree(dyn_3d_nib_in_root)
            if os.path.isdir(dyn_3d_nib_out_root): shutil.rmtree(dyn_3d_nib_out_root)
        return

    def normalization_intensity(self):
        for (input_nii_file, output_nii_file) in zip(self.smoothed_nii, self.intensity_norm_nii):
            print('run intensity normalization %s' % (input_nii_file))
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
        nib_img.to_filename(join(self.root_dir, 'dyn_group.nii'))
        return


    def diff_paired_nii(self,paired_nii_file_0, paired_nii_file_1, output_nii_file):
        print('run difference paried nii %s - %s' % (os.path.basename(paired_nii_file_0),
                                                     os.path.basename(paired_nii_file_1)))
        nib_img_0 = nib.load(paired_nii_file_0)
        np_img_0 = nib_img_0.get_data()
        nib_img_1 = nib.load(paired_nii_file_1)
        np_img_1 = nib_img_1.get_data()
        np_img = np_img_0 - np_img_1
        if np.mean(np_img_1) - np.mean(np_img_0) > 0.0: np_img = np_img_1 - np_img_0
        nib_img = nib.Nifti1Image(np_img, nib_img_0.affine)
        nib_img.to_filename(output_nii_file)
        return

