import nipype.interfaces.gift as gift
import os
import logging
import numpy as np
import nibabel as nib
from os.path import abspath, join, isdir
from glob import glob
from nilearn.image import concat_imgs

class Ica:
    # TODO: replace the matlab_cmd with whatever path specified in the docker file during installation
    matlab_cmd = '/usr/local/gift/GroupICA_standalone/run_groupica.sh /usr/local/MATLAB/mcr2016a/v901'
    algo_type = {'Infomax': 1, 'FastICA': 2, 'ERICA': 3, 'SIMBEC': 4, 'EVD': 5, 'JADE': 6,
                 'AMUSE': 7, 'SDD': 8, 'Semi_blind': 9, 'Constrained_ICA': 10}
    def __init__(self,opts):
        if opts.ica_file_directory: #TODO: select derivatives sub folder first 
            if opts.ica_include_sub_directory:
                self.in_files = glob(join(opts.ica_file_directory, 'sub*/PD_control','*.nii.gz'))
            else:
                self.in_files = glob(join(opts.ica_file_directory,"*.nii.gz"))
                # TODO: add list of files option
        elif opts.ica_file_list:
            if os.path.exists(str(opts.ica_file_list)):
                fn = str(opts.ica_file_list) 
                self.in_files = list(np.loadtxt(fn,delimiter = '\n',dtype='str'))
            else:
                self.in_files = opts.ica_file_list
        if opts.output_directory: self.output_directory = join(opts.output_directory)
        else:self.output_directory = join(opts.bids_directory,'derivatives','ica_results')
        if not os.path.exists(self.output_directory): os.makedirs(self.output_directory)
        if opts.ica_component_number != 0:  # if specify # for ica component, then set to estimation
            self.dim = opts.ica_component_number
            self.do_estimate = 0
        else:
            self.do_estimate = 1
        self.algorithm_int = self.algo_type[opts.algorithm]
        self.algorithm_name = opts.algorithm
        self.modality = opts.ica_modality
        if self.modality == 'PET':
            self.process_file = self.combine_multiple_PET_subjects() 
        else:
            self.process_file = self.in_files
        if opts.ica_temp_path: self.template = opts.ica_temp_path
        else: self.template = generate_template()
        self.log_file = join(self.output_directory,'fpetprep.log')
    
    def combine_multiple_PET_subjects(self):
        combined_img = join(self.output_directory,'combined_group.nii.gz')
        new_img = concat_imgs(self.in_files)
        nib.save(new_img, combined_img)
        return combined_img


    def run(self):
        # setup GIFT path
        gift.GICACommand.set_mlab_paths(matlab_cmd = self.matlab_cmd, use_mcr = True)
        gc = gift.GICACommand()
        gc.inputs.in_files = self.process_file
        gc.inputs.out_dir = self.output_directory
        if not self.do_estimate:
            gc.inputs.dim = self.dim
        gc.doEstimation = self.do_estimate
        print("performing " + str(self.algorithm_name) +  " now")
        gc.inputs.algoType = self.algorithm_int
        gc.inputs.mask = '/home/kejunli/git/fpetprep/fpetprep/template/mni152_brainmask_iso2mm.nii.gz' #TODO: change path 
        #os.path.join(os.path.dirname(__file__), 'template','mni152_brainmask'  + '_' + self.resolution + '.nii.gz')
        gc.inputs.refFiles = self.template
        gc_results = gc.run()
        return gc_results

    def plot_results(self):
        # TODO: figure out how to visualize/summarize the ica results
        return