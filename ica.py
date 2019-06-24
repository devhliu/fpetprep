import nipype.interfaces.gift as gift
from os.path import abspath, join

def gica(opts):
         #matlab_cmd, algorithm,num_component,estimation,reduction_step):
    # setup GIFT path
    gc = gift.GICACommand()
    matlab_cmd = "/usr/local/gift/GroupICA_standalone/run_groupica.sh /usr/local/MATLAB/MCR2016A/V901"
    # TODO: replace the matlab_cmd with whatever path specified in the docker file during installation
    # TODO: add an option in the parser.py for the user to specify the own version they want to use
    gift.GICACommand.set_mlab_paths(matlab_cmd = matlab_cmd, use_mcr = True)
    gc.inputs.in_files = opts.bids_directory
    gc.inputs.out_dir = opts.ica_directory
    if opts.ica_component_number:
        gc.inputs.dim = opts.ica_component_number
    if opts.infomax:
        print("performing infomax now")
        gc.inputs.algoType = 1
    gc_results = gc.run()
    return gc_results


