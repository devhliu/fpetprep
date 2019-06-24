import nipype.interfaces.gift as gift
import os
from os.path import abspath, join, isdir
from glob import glob

def gica(opts):
         #matlab_cmd, algorithm,num_component,estimation,reduction_step):
    # setup GIFT path
    matlab_cmd = '/usr/local/gift/GroupICA_standalone/run_groupica.sh /usr/local/MATLAB/mcr2016a/v901'
    # TODO: replace the matlab_cmd with whatever path specified in the docker file during installation
    # TODO: add an option in the parser.py for the user to specify the own version they want to use
    gift.GICACommand.set_mlab_paths(matlab_cmd = matlab_cmd, use_mcr = True)
    gc = gift.GICACommand()
    gc.inputs.in_files = glob(join(opts.file_directory,"*.nii.gz"))
    gc.inputs.out_dir = join(opts.output_directory,'ica_results')
    if not isdir(gc.inputs.out_dir): os.mkdir(gc.inputs.out_dir)
    if opts.ica_component_number:
        gc.inputs.dim = opts.ica_component_number
    print(opts.algorithm)
    if opts.algorithm[0] == 'infomax':
        print("performing infomax now")
        gc.inputs.algoType = 1
    gc_results = gc.run()
    return gc_results


