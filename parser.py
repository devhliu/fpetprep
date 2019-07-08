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
    parser.add_argument('bids_directory',action = 'store', type=str,
                        help= 'root folder for your BIDS format data')
    # options for storing output
    p_output = parser.add_argument_group('Options for specify where to store output')
    p_output.add_argument('--output_directory', required = False, action='store', default=[],type=str,
                        help='directory to store output')

    # bids conversion & suv calculation
    #TODO: add help
    p_bids_conversion = parser.add_argument_group('Options for BIDS format conversion')
    p_bids_conversion.add_argument('--heudiconv', action='store', type=str, nargs='+',help = 'use heudiconv to convert data. Pass the command directly')
    p_bids_conversion.add_argument('--generate_excel_file', action='store_true',default=False,
                                   help='scan through given directory to generate a sample excel file')
    p_bids_conversion.add_argument('--convert2bids', action='store_true', default=False)
    p_bids_conversion.add_argument('--dicom_directory', required='--convert2bids' in sys.argv or '--generate_excel_file' in sys.argv,
                                   action='store', type=str, help='root folder for dicom data')
    p_bids_conversion.add_argument('--excel_file_path',action='store', required='--convert2bids' in sys.argv, type=str)
    p_bids_conversion.add_argument('--mode', action='store', required='--generate_excel_file' in sys.argv,
                                   choices = ['one_per_dir', 'multi_per_dir'])
    p_bids_conversion.add_argument('--pattern', action='store', required='--generate_excel_file' in sys.argv)
    # bids validation
    p_bids_validate = parser.add_argument_group('Options for BIDS format validation')
    p_bids_validate.add_argument('--bids-validation', '--bids_validation',action='store_true', default=False,
                        help='validating BIDS format data')
    p_bids_validate.add_argument('--participant-label', '--participant_label', action='store', nargs='+',required='--bids_validations' in sys.argv,
                        help='a space delimited list of participant identifiers or a single '
                             'identifier (the sub-prefix can be removed')
    # MNI
    p_mni = parser.add_argument_group('Options for MNI')
    p_mni.add_argument('--mni',action = 'store_true', default = False,
                       help = 'perform spatial normalization onto MNI space')
    p_mni.add_argument('--mni_include_sub_directory', action='store_true', default=False,
                       help='include files in the sub-directory, make sure subject root directory start with sub')
    p_mni.add_argument('--resolution', required='--mni' in sys.argv, action='store',default=[],
                       choices = ['iso1mm','iso2mm'])
    p_mni.add_argument('--save_intermediate_files', action='store_true', default=False)
    # TODO: add help
    p_mni.add_argument('--gaussian_filter', required = '--mni' in sys.argv, action='store',type=int,nargs=3,
                       help="gaussian filter for smoothing in the format of x x x where x could be any integer value")
    # SUVR
    p_suvr = parser.add_argument_group('Options for SUVR')
    p_suvr.add_argument('--suvr',action ='store_true',default=False,
                        help='Evaluating standard uptake value ratio')

    #TODO: implement suvr

    # PVC
    p_pvc = parser.add_argument_group('Options for partial volume correction')
    p_pvc.add_argument('--pvc', action='store_true', default=False, help='perform partial volume correction')
    p_pvc.add_argument('--pvc_mm', action='store', required= '--pvc' in sys.argv, type=int, nargs=3, help='')  #TODO: fix this later
    # TODO: add help
    # ica analysis
    p_ica = parser.add_argument_group('Options for running ICA ')
    p_ica.add_argument('--ica', required=False, action ='store_true')
    p_ica.add_argument('--ica_file_directory',required=False,action='store',type=str)
    p_ica.add_argument('--ica_include_sub_directory', action='store_true', default=False,
                       help='include files in the sub-directory, make sure subject root directory start with sub')
    p_ica.add_argument('--ica_file_list',required= '--ica' in sys.argv and '--ica_file_directory' not in sys.argv,action='store',type=str)
    p_ica.add_argument('--ica_modality',required = False, action='store',default='PET',choices = ['PET','MR'])
    p_ica.add_argument('--algorithm', required=False, action ='store', default='Infomax',
                       choices=['Infomax','FastICA','Constrained_ICA','ERICA', 'SIMBEC', 'EVD', 'JADE','AMUSE', 'SDD', 'Semi_blind'],
                       help='which ICA algorithm to use')
    p_ica.add_argument('--ica-component-number','--ica_component_number',action='store', default=0, type=int,
                       help='specify the number of components') #TODO: if 0, then do estimation
    return parser


def main():
    opts = get_parser().parse_args()
    if not len(sys.argv) > 1:
        print("please select a valid analysis")
        return
    if not opts.output_directory:
        opts.output_directory = opts.bids_directory
    if opts.heudiconv:
        print(opts.heudiconv)
        os.system(opts.heudiconv)
    if opts.generate_excel_file:
        print("generating excel file")
        gen_excel = Dcm2bids(opts)
        gen_excel.generate_excel_file()
    if opts.convert2bids:
        print("converting to BIDS format")
        cov_2_bids = Dcm2bids(opts)
        cov_2_bids.run()
     if opts.bids_validation:
            print('Validating BIDS format')
            exec_env = os.name
            validate_input_dir(exec_env, opts.file_directory, opts.participant_label)
    if opts.mni:
        pet_mni = Mni(opts)
        pet_mni.run()
    if opts.ica:
        print("selected " + str(opts.algorithm) + ' for ICA analysis')
        if opts.ica_component_number:
            print('the number of ICA component: ' + str(opts.ica_component_number))
        pet_ica = Ica(opts)
        ica_results = pet_ica.run()
    return


if __name__ == "__main__":
    main()
