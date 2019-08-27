import os
from pathlib import Path
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import sys
from ica import Ica
from mni import Mni
from suvr import Suvr
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
    p_general = parser.add_argument_group('Options for specify where to store output')
    p_general.add_argument('--output_directory', required = False, action='store', default='',type=str,
                        help='directory to store output')
    p_general.add_argument('--resolution', required=False, action='store',default=['iso2mm'],
                       choices = ['iso1mm','iso2mm'])
    # bids conversion & suvr calculation
    p_bids_conversion = parser.add_argument_group('Options for BIDS format conversion')
    p_bids_conversion.add_argument('--heudiconv', action='store', type=str, nargs='+',help = 'use heudiconv to convert your data to BIDS format. Pass the command directly')
    p_bids_conversion.add_argument('--generate_excel_file', action='store_true',default=False,
                                   help='scan through given directory to generate a sample excel file') 
    p_bids_conversion.add_argument('--convert2bids', action='store_true', default=False) #if select this, also need to pass the excel file path, dicom directory
    p_bids_conversion.add_argument('--dicom_directory', required='--convert2bids' in sys.argv or '--generate_excel_file' in sys.argv,
                                   action='store', type=str, help='root folder for dicom data')
    p_bids_conversion.add_argument('--excel_file_path',action='store', required='--convert2bids' in sys.argv, type=str)
    p_bids_conversion.add_argument('--mode', action='store', required='--generate_excel_file' in sys.argv,
                                   choices = ['one_per_dir', 'multi_per_dir'],help ='specify whether there is only one .dcm file in the directory or multiple') 
    p_bids_conversion.add_argument('--pattern', action='store', required='--generate_excel_file' in sys.argv and 'one_per_dir' in sys.argv)
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
    p_mni.add_argument('--save_intermediate_files', action='store_true', default=False)
    p_mni.add_argument('--gaussian_filter', required = '--mni' in sys.argv, action='store',type=int,nargs=3,
                       help="gaussian filter for smoothing in the format of n n n where n could be any integer value") # example: 3 3 3 
    # SUVR
    p_suvr = parser.add_argument_group('Options for SUVR')
    p_suvr.add_argument('--suvr',action ='store_true',default=False,
                        help='Evaluating standard uptake value ratio')
    # PVC uncomment this when it is implemented
    #p_pvc = parser.add_argument_group('Options for partial volume correction')
    #p_pvc.add_argument('--pvc', action='store_true', default=False, help='perform partial volume correction')
    #p_pvc.add_argument('--pvc_mm', action='store', required= '--pvc' in sys.argv, type=int, nargs=3, help='')  
    # ica analysis
    p_ica = parser.add_argument_group('Options for running ICA ')
    p_ica.add_argument('--group_ica_type',required = False, action = 'store',default='spatial',choices = ['spatial','temporal'])
    #p_ica.add_argument('--ica_temp',required=False,action='store_true') see comment below
    p_ica.add_argument('--ica_temp_path',required=False,default=[],action='store',type=str)
    p_ica.add_argument('--ica', required=False, action ='store_true')
    p_ica.add_argument('--ica_file_directory',required=False,action='store',type=str)
    p_ica.add_argument('--ica_include_sub_directory', action='store_true', default=False,
                       help='include files in the sub-directory, make sure subject root directory start with sub')
    p_ica.add_argument('--ica_file_list',required= ('--ica' in sys.argv or '--ica_temp' in sys.argv) and '--ica_file_directory' not in sys.argv,action='store',type=str)
    p_ica.add_argument('--ica_modality',required = False, action='store',default='PET',choices = ['PET','MR'])
    p_ica.add_argument('--algorithm', required=False, action ='store', default='Infomax',
                       choices=['Infomax','FastICA','Constrained_ICA','ERICA', 'SIMBEC', 'EVD', 'JADE','AMUSE', 'SDD', 'Semi_blind'],
                       help='which ICA algorithm to use')
    p_ica.add_argument('--ica-component-number','--ica_component_number',action='store', default=0, type=int,
                       help='specify the number of components') #TODO: if 0, then do estimation
    return parser


def handle_parsed_input(opts):
    if not len(sys.argv) > 1:
        print("please select a valid analysis") #make sure both directory and analysis is selected
        return
    if opts.heudiconv: #if user want to use heudiconv, they need to write their own command line
        print(opts.heudiconv)
        os.system(opts.heudiconv)
    if opts.generate_excel_file: #generate excel file for BIDS conversion
        print("generating excel file")
        gen_excel = Dcm2bids(opts)
        gen_excel.generate_excel_file()
    if opts.convert2bids: #convert to BIDS, need to provide excel file path --> UI: need to send output to an excel file
        print("converting to BIDS format")
        cov_2_bids = Dcm2bids(opts)
        cov_2_bids.run()
    if opts.bids_validation: #validate BIDS format; almost never necessary and never tested
        print('Validating BIDS format')
        exec_env = os.name
        validate_input_dir(exec_env, opts.file_directory, opts.participant_label)
    if opts.mni: # mni normalization --> for a group of scans, normalize spatially to the same template -> specified 
        pet_mni = Mni(opts)
        pet_mni.run()
    #if opts.ica_temp:# generate tecmplate for ICA (Independent Component Analysis), uncomment when actually implemented, rough structure can be found in ica_utils.py
    #    ica_temp = Ica(opts)
    #    ica_temp.generate_ica_template()
    if opts.suvr: #standarized uptake value ratio 
        suvr = Suvr(opts) #normal patient ratio over brainstem; Other patient need different region as baseline --> not yet suppoted
        suvr.run()
    if opts.ica: #different algorithms can be used for ICA, optional: specify the numbe of ICs 
        print("selected " + str(opts.algorithm) + ' for ICA analysis')
        if opts.ica_component_number:
            print('the number of ICs: ' + str(opts.ica_component_number))
        pet_ica = Ica(opts)
        ica_results = pet_ica.run()
    return


if __name__ == "__main__":
    opts = get_parser().parse_args() 
    handle_parsed_input(opts)
