import nipype.interfaces.gift as gift
import os
from os.path import abspath, join, isdir
from glob import glob


class Ica:
    # TODO: replace the matlab_cmd with whatever path specified in the docker file during installation
    # TODO: add an option in the parser.py for the user to specify the path of the specfic GIFT version they want to use
    matlab_cmd = '/usr/local/gift/GroupICA_standalone/run_groupica.sh /usr/local/MATLAB/mcr2016a/v901'
    algo_type = {'Infomax': 1, 'FastICA': 2, 'ERICA': 3, 'SIMBEC': 4, 'EVD': 5, 'JADE': 6,
                 'AMUSE': 7, 'SDD': 8, 'Semi_blind': 9, 'Constrained_ICA': 10}
    def __init__(self,opts):
        self.in_files = glob(join(opts.file_directory, "*.nii.gz"))
        self.out_dir = join(opts.output_directory, 'ica_results')
        if not isdir(self.out_dir): os.mkdir(self.out_dir)
        if opts.ica_component_number:
            self.dim = opts.ica_component_number
        self.algorithm_int = self.algo_type[opts.algorithm]
        self.algorithm_name = opts.algorithm


    def run(self):
        # setup GIFT path
        gift.GICACommand.set_mlab_paths(matlab_cmd = self.matlab_cmd, use_mcr = True)
        gc = gift.GICACommand()
        gc.inputs.in_files = self.in_files
        gc.inputs.out_dir = self.out_dir
        if self.dim:
            gc.inputs.dim = self.dim
        print("performing " + str(self.algorithm_nameal) +  " now")
        gc.inputs.algoType = self.algorithm_int
        gc_results = gc.run()
        return gc_results

    def plot_results(self):
        # TODO: figure out how to visualize/summarize the ica results