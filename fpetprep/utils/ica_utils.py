import os
import numpy as np
import nibabel as nib
from os.path import abspath, join, isdir, basename
from glob import glob
from nilearn.image import concat_imgs
import logging, shutil
import shutil, re
import difflib, pydicom
import pandas as pd
from pandas import ExcelFile
from pydicom.misc import is_dicom

def Noise_rest(root_dir):
    rest_list = glob(join(root_dir, 'sub*/staticPET',"*rest*.nii.gz"))
    noise_list = glob(join(root_dir, 'sub*/staticPET',"*noise*.nii.gz"))
    eg = nib.load(rest_list[0])
    for (rest_file,noise_file) in zip(rest_list,noise_list):
        rest = nib.load(rest_file).get_data()
        noise = nib.load(noise_file).get_data()
        rel_val = noise - rest
        out = nib.Nifti1Image(rel_val, eg.affine)
        rel_file = rest_file.replace('rest','rel')
        out.to_filename(rel_file)
    return



def copy_file():
    file_list = glob(join('/home/kejunli/data/PD_PTCT/dcm','*','*','2.44*','*.dcm'))
    #file_list = glob(join("/home/kejunli/data/PD_PTCT/dcm/PD_control/li jia le_020234563_122000/1","*"))
    #file_list = glob(join('/home/kejunli/BraTS2019Data/Training/LGG','*','*.nii.gz'))
    file_rep = [file.replace(' ','') for file in file_list]
    file_rep = [file.replace('PD_PTCT','PD_PT_only') for file in file_rep]
    #file_rep = [join('/home/kejunli/BraTS2019Data/Training/LGG',basename(file)) for file in file_list]
    file_rep = [file + '.dcm' for file in file_rep]

    for (src,dest) in zip(file_list,file_rep):
        dir_name = os.path.dirname(dest)
        if not os.path.exists(dir_name): os.makedirs(dir_name)
        shutil.copy(src,dest)



def edit_xlsx(xlsx_file):
    xls = ExcelFile(xlsx_file)
    df = xls.parse(xls.sheet_names[0])
    descrips = df['08_SeriesRoot'].to_list()
    func_list = []
    task_list = []
    for descrip in descrips:
        if descrip.find('PD_control') != -1:
            taskName = 'control'
            funcName = 'PD_control'
        else:
            taskName = 'PD'
            funcName = 'PD'
        func_list.append(funcName)
        task_list.append(taskName)
    df['11_Func'] = func_list
    df['12_Task'] = task_list
    df.to_excel(xlsx_file)
    return func_list, task_list

def generate_template(temp_file_name):
        in_files = glob(join('/home/kejunli/data/PD-bids/derivatives/suvr', 'sub*/PD_control',"*.nii.gz"))
        #in_files.extend(glob(join('/home/kejunli/data/test/bids_dir/derivatives/suvr', 'sub*/staticPET',"*noise*.nii.gz")))
        out_dir =  join('/home/kejunli/data/PD-bids/derivatives/','ica_results')
        log_file = join(out_dir,'fpetprep.log')
        eg = nib.load(in_files[0])
        sumV = np.zeros(eg.get_data().shape)
        for file in in_files:
            try:
                pet = nib.load(file).get_data()
                sumV = sumV + pet
            except ValueError as err:
                printMessage = 'Dimension mismatch %s.'%(file)
                print(printMessage)
                logging.basicConfig(filename=log_file, level=logging.DEBUG, 
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
                logger=logging.getLogger(__name__)
                #logger.info( )
                logger.error(printMessage + '\n\t The specific error is: ' + str(err))
        avg = sumV /len(in_files)
        print(len(in_files))
        out = nib.Nifti1Image(avg, eg.affine)
        output_nii_file = join(out_dir,'generated_temp',temp_file_name +'.nii.gz')
        dir_name = os.path.dirname(output_nii_file)
        if not os.path.exists(dir_name): os.makedirs(dir_name)
        out.to_filename(output_nii_file)
        return
#edit_xlsx('/home/kejunli/data/PD-bids/PD.xlsx')

#generate_template('PET_PD_control_temp')
copy_file()