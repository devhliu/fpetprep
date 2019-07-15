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
        if opts.ica_file_directory: 
            if opts.ica_include_sub_directory:
                self.in_files = glob(join(opts.ica_file_directory, 'sub*/staticPET',"*.nii.gz"))
            else:
                self.in_files = glob(join(opts.ica_file_directory,"*.nii.gz"))
                # TODO: add list of files option
        elif opts.ica_file_list:
            if os.path.exists(str(opts.ica_file_list)):
                fn = str(opts.ica_file_list) 
                self.in_files = list(np.loadtxt(fn,delimiter = '\n',dtype='str'))
            else:
                self.in_files = opts.ica_file_list
        if opts.output_directory: self.out_dir = join(opts.output_directory)
        else:join(opts.bids_directory,'derivatives','ica_results')
        if not os.path.exists(self.out_dir): os.makedirs(self.out_dir)
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
    
    def combine_multiple_PET_subjects(self):
        combined_img = join(self.out_dir,'combined_group.nii.gz')
        new_img = concat_imgs(self.in_files)
        nib.save(new_img, combined_img)
        return combined_img


    def generate_template(temp_file_name):
        eg = nib.load(self.in_files[0])
        sumV = zero(eg.get_data().shape)
        for file in self.in_files:
            try:
                pet = nib.load(file)
                sumV = sumV + pet
            except valueError as err:
                printMessage = 'Dimension mismatch %s.'%(file)
                print(printMessage)
                logging.basicConfig(filename=self.log_file, level=logging.DEBUG, 
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
                logger=logging.getLogger(__name__)
                #logger.info( )
                logger.error(printMessage + '\n\t The specific error is: ' + str(err))
        avg = sumV /len(self.in_files)
        out = nib.Nifti1Image(avg, eg.affine)
        out.to_filename(join(self.out_dir,'generate_template','temp_file_name','.nii.gz'))
        return

    def run(self):
        # setup GIFT path
        gift.GICACommand.set_mlab_paths(matlab_cmd = self.matlab_cmd, use_mcr = True)
        gc = gift.GICACommand()
        gc.inputs.in_files = self.process_file
        gc.inputs.out_dir = self.out_dir
        if not self.do_estimate:
            gc.inputs.dim = self.dim
        gc.doEstimation = self.do_estimate
        print("performing " + str(self.algorithm_name) +  " now")
        gc.inputs.algoType = self.algorithm_int
        gc.inputs.mask = '/home/kejunli/git/fpetprep/fpetprep/template/mni152_brainmask_iso2mm.nii.gz'
        gc.inputs.refFiles = self.template
        gc_results = gc.run()
        return gc_results

    def plot_results(self):
        # TODO: figure out how to visualize/summarize the ica results
        return