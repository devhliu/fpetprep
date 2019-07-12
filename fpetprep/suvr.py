#adapt from quantification)method_suvr.py from APPIAN 
#(https://github.com/APPIAN-PET/APPIAN/blob/7f1ae274ac0788bb0d68320f3a730462a5ad56ed/Quantification/methods/quant_method_suvr.py)
import numpy as np
import json, os
import nibabel as nib
from Extra.utils import splitext
from quantification_template import *
from scipy.integrate import simps
in_file_format="NIFTI"
out_file_format="NIFTI"
reference=True
voxelwise=True

class suvr:
    _suffix = "_suvr" 
    def __init__(self, opts):
        self.input_dir = str(opts.bids_directory)
        self.output_dir = join(str(opts.output_directory),'derivatives','suvr')
        self.out_file =
        self.in_file
        self.referencef


     def generate_file_list(self, basefile, _suffix):
        if not isdir(self.output_dir):
            os.makedirs(self.output_dir)
        suvr_nii = []
        for file in self.input_nii:
            file_dir, file_name = os.path.split(file)
            file_com = file_dir.split(os.sep)
            root_com = str(self.input_dir).split(os.sep)
            new_com = [i for i in file_com if i not in root_com]
            suvr = join(self.output_dir,*new_com, file_name)
            suvr_nii.append(normalized)
        return suvr_nii

    def run(self):
        if not isdefined(self.out_file) : 
            self.out_file = self._gen_output(self.in_file, self._suffix)
        header = json.load(open(self.header, "r") )
        pet = nib.load(self.in_file).get_data()
        reference_vol = nib.load(self.reference)
        reference = reference_vol.get_data()
        ndim = len(pet.shape)
        
        vol = pet
        if ndim > 3 :
            if not isdefined(self.start_time) : 
                start_time=0
            else :
                start_time=self.start_time

            if not isdefined(self.end_time) : 
                end_time=header['Time']['FrameTimes']['Values'][-1][1]
            else :
                end_time=self.end_time

            try : 
                time_frames = [ float(s) for s,e in  header['Time']["FrameTimes"]["Values"] if s >= start_time and e <= end_time ]
            except ValueError :
                time_frames = [1.]
            vol = simps( pet, time_frames, axis=3)
        
        idx = reference > 0
        ref = np.mean(vol[idx])
        print("SUVR Reference = ", ref)
        vol = vol / ref
        
        out = nib.Nifti1Image(vol, reference_vol.affine)
        out.to_filename(self.out_file)

        return runtime