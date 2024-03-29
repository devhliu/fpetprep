#adapt from quantification_method_suvr.py from APPIAN 
#(https://github.com/APPIAN-PET/APPIAN/blob/7f1ae274ac0788bb0d68320f3a730462a5ad56ed/Quantification/methods/quant_method_suvr.py)
import numpy as np
import json, os, sys
import nibabel as nib
from os.path import join, isdir, basename, splitext, dirname
from scipy.integrate import simps
from pathlib import Path
in_file_format="NIFTI"
out_file_format="NIFTI"
reference=True
voxelwise=True

class Suvr:
    _suffix = "_suvr" 
    def __init__(self, opts):
        self.resolution = opts.resolution
        self.input_dir = str(opts.bids_directory)
        if opts.output_directory:
            self.output_dir = str(opts.output_directory)
        else:
            self.output_dir =join(str(opts.bids_directory),'derivatives','suvr')
        suvbw_list = glob(input_dir +'/**/*SUVbw.nii.gz',recursive=True)
        if len(suvbw_list) == 0:
            print('please use convert2bids to convert your dcm files to BIDs first')
            sys.exit()
        else:
            self.input_nii = [str(file) for file in suvbw_list]
        self.reference = self.get_mni152_nii_file()

    def get_mni152_nii_file(self):
        return os.path.join(os.path.dirname(__file__), 'template',
                            'mni152_' + 'brainstemmask' + '_' + self.resolution + '.nii.gz')

    def run(self):
        if not isdir(self.output_dir):
            os.makedirs(self.output_dir)
        for input_nii_file in self.input_nii:
            output_nii_file = file.replace('mni_intensity','suvr')
            print('run %s' % input_nii_file)
            print('generate %s' % output_nii_file)
            if os.path.exists(output_nii_file): continue
            dir_name = os.path.dirname(output_nii_file)
            if not os.path.exists(dir_name): os.makedirs(dir_name)
            base_file_name, _ = splitext(basename(input_nii_file))
            pet = nib.load(input_nii_file).get_data()
            reference_vol = nib.load(self.reference)
            reference = reference_vol.get_data()
            ndim = len(pet.shape)
            vol = pet            
            idx = reference > 0
            ref = np.mean(vol[idx])
            print("SUVR Reference = ", ref)
            vol = vol / ref
            out = nib.Nifti1Image(vol, reference_vol.affine)
            out.to_filename(output_nii_file)
            json_file = output_nii_file.replace('.nii.gz', '.json')
            with open(json_file, 'wt', encoding='utf-8') as f_json:
                json.dump({'suvr_factor': str(ref)},
                      f_json,indent=4)
        return 

