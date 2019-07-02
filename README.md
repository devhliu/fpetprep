fpetprep
==============
usage
--------------
      docker run [-h] [--generate_excel_file] [--convert2bids]
                 [--dicom_directory DICOM_DIRECTORY]
                 [--excel_file_path EXCEL_FILE_PATH]
                 [--mode {one_per_dir,multi_per_dir}] [--pattern PATTERN]
                 [--participant-label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
                 [--skip-bids-validation] [--mni]
                 [--mni_include_sub_directory] [--resolution {iso1mm,iso2mm}]
                 [--gaussian_filter GAUSSIAN_FILTER GAUSSIAN_FILTER GAUSSIAN_FILTER]
                 [--suvr] [--pvc] [--pvc_mm PVC_MM PVC_MM PVC_MM] [--ica]
                 [--algorithm {Infomax,FastICA,Constrained_ICA}]
                 [--ica-component-number ICA_COMPONENT_NUMBER]
                 bids_directory output_directory


    positional arguments:
      bids_directory        root folder for your BIDS format data
      output_directory      directory to store output

    optional arguments:
      -h, --help            show this help message and exit
    
    Options for BIDS format conversion:
      --generate_excel_file
                            scan through given directory to generate a sample excel file
      --convert2bids
      --dicom_directory DICOM_DIRECTORY
                            root folder for dicom data
      --excel_file_path EXCEL_FILE_PATH
      --mode {one_per_dir,multi_per_dir}
      --pattern PATTERN
    
    Options for BIDS format validation:
      --participant-label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...], --participant_label PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]
                            a space delimited list of participant identifiers or a single identifier (the sub-prefix can be removed
      --skip-bids-validation, --bids_validation
                            validating BIDS format data
    
    Options for MNI:
      --mni                 perform spatial normalization onto MNI space
      --mni_include_sub_directory
                            include files in the sub-directory
      --resolution {iso1mm,iso2mm}
      --gaussian_filter GAUSSIAN_FILTER GAUSSIAN_FILTER GAUSSIAN_FILTER
                            gaussian filter for smoothing in the format of x x x where x could be any integer value
    
    Options for SUVR:
      --suvr                Evaluating standard uptake value ratio
    
    Options for partial volume correction:
      --pvc                 perform partial volume correction
      --pvc_mm PVC_MM PVC_MM PVC_MM
    
    Options for running ICA :
      --ica
      --algorithm {Infomax,FastICA,Constrained_ICA}
                            which ICA algorithm
      --ica-component-number ICA_COMPONENT_NUMBER, --ica_component_number ICA_COMPONENT_NUMBER
                            specify the number of components
