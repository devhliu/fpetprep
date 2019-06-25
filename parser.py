import os
from pathlib import Path
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import sys
from ica import Ica
from mni import mni
from utils.bids import validate_input_dir
from workflow import initiate_workflow


def get_parser():
    parser = ArgumentParser(description='fPETPrep: PET pre-processing workflow',
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('file_directory',action = 'store', type=Path,
                        help= 'root folder for your BIDS format data')
    parser.add_argument('output_directory', action='store', type=Path,
                        help='directory to store output')
    parser.add_argument('type', action='store')

    # bids validation
    p_bids = parser.add_argument_group('Options for BIDS format validation')
    p_bids.add_argument('--participant-label', '--participant_label', action='store', nargs='+',
                        help='a space delimited list of participant identifiers or a single '
                             'identifier (the sub-prefix can be removed')
    p_bids.add_argument('--skip-bids-validation', '--bids_validation',action='store_true', default=False,
                        help='validating BIDS format data')
    # MNI
    p_mni = parser.add_argument_group('Options for MNI')
    p_mni.add_argument('--mni',action = 'store_true', default = False,
                       help = 'perform spatial normalization onto MNI space')
    p_mni.add_argument('--resolution', required='--mni' in sys.argv, action='store',default=[],
                       choices = ['iso1mm','iso2mm'])
    p_mni.add_argument('--gaussian_filter',action='store',type=int,nargs=3,
                       help="gaussian filter for smoothing in the format of x x x where x could be any integer value")
    # SUVR
    p_suvr = parser.add_argument_group('Options for SUVR')
    p_suvr.add_argument('--suvr',action ='store_true',default=False,help='Evaluating standard uptake value ratio')

    # PVC
    # -optional for now; add later if actually decide to implement it

    # ica analysis
    p_ica = parser.add_argument_group('Options for running ICA ')
    p_ica.add_argument('--ica', required=False, action ='store_true')
    p_ica.add_argument('--algorithm', required=False, action ='store',default=[],
                       choices=['Infomax','FastICA','Constrained_ICA'],
                       help='which ICA algorithm')
    p_ica.add_argument('--ica-component-number','--ica_component_number',action='store', default=0, type=int,
                       help='specify the number of components')
    return parser


def main():
    opts = get_parser().parse_args()
    # TODO: add these in build_workflow; BIDS related action-item --> around line 380
    #if opts.bids_conversion:
    #    print('converting your data to BIDS format')
    exec_env = os.name

    #TODO: use default parameters if not specified
    if not opts.type:
        opts.type = 'pet'
    if not opts.skip_bids_validation:
        print('Validating BIDS format')
        validate_input_dir(exec_env,opts.file_directory,opts.participant_label)
    if opts.mni:
        pet_mni = mni(opts)
        pet_mni.run()
    if opts.suvr:
        # do something
        print("processing SUV")
    if opts.ica:
        print("selected " + str(opts.algorithm) + ' for ICA analysis')
        if opts.ica_component_number:
            print('the number of ICA component: ' + str(opts.ica_component_number))
        pet_ica = Ica(opts)
        ica_results = pet_ica.run()
    else:
        print("please select a valid analysis")


main()
