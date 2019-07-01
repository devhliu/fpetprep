from nipype.interfaces.petpvc import PETPVC
from os.path import join,basename,splitext

def init(opts):
    pvc = PETPVC()
    pvc.inputs.in_file = opts.input_pvc_file #'pet.nii.gz'
    pvc.inputs.mask_file = opts.pvc_mask_file #'tissues.nii.gz'
    pvc.inputs.pvc = opts.pvcType #'RBV'
    pvc.inputs.out_file = join(opts.output_dir, splitext(basename(opts.input_pvc_file))[0].rstrip('.nii')
                               +'pet_pvc_' + opts.pvcType + '.nii.gz') #'pet_pvc_rbv.nii.gz'
    pvc.inputs.fwhm_x = 2.0
    pvc.inputs.fwhm_y = 2.0
    pvc.inputs.fwhm_z = 2.0
    return

def run(pvc):
    outs = pvc.run()  # doctest: +SKIP
    return outs