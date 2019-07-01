import os
from pathlib import Path
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import sys
from ica import Ica
from mni import Mni
from dcm2bids.udcm2bids import Dcm2bids
#from utils.bids_validate import validate_input_dir
#bids validator is commented for now
#from workflow import initiate_workflow



def get_parser():
    parser = ArgumentParser(description='fPETPrep: PET pre-processing workflow',
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('bids_directory',action = 'store', type=Path,
                        help= 'root folder for your BIDS format data')
    parser.add_argument('output_directory', action='store', type=Path,
                        help='directory to store output')

    # bids conversion & suv calculation
    #TODO: add help
    p_bids_conversion = parser.add_argument_group('Options for BIDS format conversion')
    p_bids_conversion.add_argument('--generate_excel_file', action='store_true',default=False,
                                   help='scan through given directory to generate a sample excel file')
    p_bids_conversion.add_argument('--convert2bids', action='store_true', default=False)
    p_bids_conversion.add_argument('--dicom_directory', required='--convert2bids' in sys.argv,
                                   action='store', type=Path, help='root folder for dicom data')
    p_bids_conversion.add_argument('--excel_file_path',action='store', required='--convert2bids' in sys.argv, type=Path)
    p_bids_conversion.add_argument('--mode', action='store', required='--generate_excel_file' in sys.argv,
                                   choices = ['one_per_dir', 'multi_per_dir'])
    p_bids_conversion.add_argument('--pattern', action='store', required='--generate_excel_file' in sys.argv
                                   )
    # bids validation
    p_bids_validate = parser.add_argument_group('Options for BIDS format validation')
    p_bids_validate.add_argument('--participant-label', '--participant_label', action='store', nargs='+',
                        help='a space delimited list of participant identifiers or a single '
                             'identifier (the sub-prefix can be removed')
    p_bids_validate.add_argument('--skip-bids-validation', '--bids_validation',action='store_true', default=False,
                        help='validating BIDS format data')
    # MNI
    p_mni = parser.add_argument_group('Options for MNI')
    p_mni.add_argument('--mni',action = 'store_true', default = False,
                       help = 'perform spatial normalization onto MNI space')
    p_mni.add_argument('--mni_include_sub_directory', action='store_true', default=False,
                       help='include files in the sub-directory')
    p_mni.add_argument('--resolution', required='--mni' in sys.argv, action='store',default=[],
                       choices = ['iso1mm','iso2mm'])
    # TODO: add help
    p_mni.add_argument('--gaussian_filter', required = '--mni' in sys.argv, action='store',type=int,nargs=3,
                       help="gaussian filter for smoothing in the format of x x x where x could be any integer value")
    # SUVR
    p_suvr = parser.add_argument_group('Options for SUVR')
    p_suvr.add_argument('--suvr',action ='store_true',default=False,
                        help='Evaluating standard uptake value ratio')

    # PVC
    p_pvc = parser.add_argument_group('Options for partial volume correction')
    p_pvc.add_argument('--pvc', action='store_true', default=False, help='perform partial volume correction')
    p_pvc.add_argument('--pvc_mm', action='store', type=int, nargs =3, help='')  #TODO: fix this later
    # TODO: add help
    # ica analysis
    p_ica = parser.add_argument_group('Options for running ICA ')
    p_ica.add_argument('--ica', required=False, action ='store_true')
    p_ica.add_argument('--algorithm', required=False, action ='store',default='Infomax',
                       choices=['Infomax','FastICA','Constrained_ICA'],
                       help='which ICA algorithm') #TODO: could add more choices here
    p_ica.add_argument('--ica-component-number','--ica_component_number',action='store', default=0, type=int,
                       help='specify the number of components') #TODO: if 0, then do estimation
    return parser


def main():
    opts = get_parser().parse_args()
    if not len(sys.argv) > 4:
        print("please select a valid analysis")
        return
    if not opts.convert2bids:
        if not opts.skip_bids_validation:
            print('Validating BIDS format')
            exec_env = os.name
        #validate_input_dir(exec_env, opts.file_directory, opts.participant_label)
        #uncomment this later
    if opts.generate_excel_file:
        print("generating excel file")
        gen_excel = Dcm2bids(opts)
        gen_excel.generate_excel_file()
    if opts.convert2bids:
        print("converting to BIDS format")
        cov_2_bids = Dcm2bids(opts)
        cov_2_bids.run()
    if opts.mni:
        print("run mni")
        pet_mni = Mni(opts)
        pet_mni.run()
    if opts.ica:
        print("selected " + str(opts.algorithm) + ' for ICA analysis')
        if opts.ica_component_number:
            print('the number of ICA component: ' + str(opts.ica_component_number))
        pet_ica = Ica(opts)
        ica_results = pet_ica.run()


main()
