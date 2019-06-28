from nipype.interfaces.petpvc import PETPVC


def init(opts):
    pvc = PETPVC()
    pvc.inputs.in_file = opts.input_pvc_file #'pet.nii.gz'
    pvc.inputs.mask_file = opts.pvc_mask_file #'tissues.nii.gz'
    pvc.inputs.out_file = opts.output_pvc_file #'pet_pvc_rbv.nii.gz'
    pvc.inputs.pvc = 'RBV'
    pvc.inputs.fwhm_x = 2.0
    pvc.inputs.fwhm_y = 2.0
    pvc.inputs.fwhm_z = 2.0
    outs = pvc.run() #doctest: +SKIP
    return outs