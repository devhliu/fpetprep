from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from ica import gica

def get_parser():
    parser = ArgumentParser(description='fPETPrep: PET pre-processing workflow',
                            formatter_class=RawTextHelpFormatter)
    # bids conversion
    p_bids = parser.add_argument_group('Options for BIDS format conversion & validation')
    #p_bids.add_argument('--bids-conversion','--bids_conversion',action = 'store_true', default=False,
    #                    help='converting your data to be in BIDS format')
    p_bids.add_argument('--bids-validation', '--bids_validation',action='store_true', default=False,
                        help='validating BIDS format data')
    # MNI
    p_mni = parser.add_argument_group('Options for MNI')
    p_mni.add_argument('--mni',action = 'store_true', default = False, help = 'perform spatial normalization onto MNI space')

    # SUVR
    p_suvr = parser.add_argument_group('Options for SUVR')
    p_suvr.add_argument('--suvr',action ='store_true',default=False,help='Evaluating standard uptake value ratio')

    # PVC
    # -optional for now; add later if actually decide to implement it

    # ica analysis
    p_ica = parser.add_argument_group('Options for running ICA ')
    p_ica.add_argument('--infomax','--infomax',action = 'store_true', default=False,
                       help='performing infomax')
    p_ica.add_argument('--ica-component-number','--ica_component_number',action='store', default=0, type=int,
                       help='specify the number of components')
    return parser


def main():
    opts = get_parser().parse_args()
    # TODO: add these in build_workflow; BIDS related action-item --> around line 380
    #if opts.bids_conversion:
    #    print('converting your data to BIDS format')

    if opts.bids_validation:
        print('Validating your data are indeed in BIDS format')
     

    if opts.infomax:
        print("added ICA for your analysis")
        if opts.ica_component_number:
            print(str(opts.ica_component_number))
        gica(opts)
    else:
        print("no analysis selected")


main()