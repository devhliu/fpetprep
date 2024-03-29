import os,ast
from os import mkdir
from os.path import join, isdir, split, basename
import json
import logging
import math
import pydicom
import subprocess
import numpy as np
import nibabel as nib
from .udcmview import dump_series2xlsx, dump_xlsx2dict
from glob import glob
from datetime import datetime
from datetime import timedelta

#from .dcm2niix import dcm2niix


class Dcm2bids:
    def __init__(self, opts):
        if not isdir(str(opts.dicom_directory)):
            print("please provide a valid directory for dicom files")
            #TODO: exit the porgram here
            return
        self.dicom_root = str(opts.dicom_directory)
        self.bids_root = str(opts.bids_directory)
        if not opts.output_directory: opts.output_directory = opts.bids_directory
        self.log_file = join(opts.output_directory,'fpetprep.log')
        if not isdir(self.bids_root): mkdir(self.bids_root)
        head, tail = split(opts.excel_file_path)
        if not head: self.xlsx_file = join(opts.output_directory,opts.excel_file_path)
        else: self.xlsx_file = opts.excel_file_path
        self.mode = opts.mode
        if opts.pattern: self.pattern = opts.pattern
        else: self.pattern = '000001.dcm'

    def generate_excel_file(self):
        dump_series2xlsx(self.dicom_root, self.xlsx_file, self.mode,self.pattern)

    def run(self):
        print(self.xlsx_file)
        self.bids_func_info = dump_xlsx2dict(self.xlsx_file)
        #generic_file_list, suvbw_file_list = self.convert_uih_dcm_2_bids()
        self.convert_uih_dcm_2_bids()
        #self.generic_file_list = generic_file_list
        #self.suvbw_file_list =suvbw_file_list
        return

    def _diff_datetime(self,datetime_0, datatime_1):
        """
        :param datetime_0:
        :param datatime_1:
        :return:
        """
        acq_datetime_0 = datetime.strptime(datetime_0, '%Y%m%d%H%M%S')
        acq_datetime_1 = datetime.strptime(datatime_1, '%Y%m%d%H%M%S')
        delta_secs = acq_datetime_1 - acq_datetime_0
        return delta_secs.total_seconds()

    # ----------------------------------------------------------------------------------------
    #
    def _calc_uih_pet_suvbw_factor(self,ds):
        """
        :param ds:  pydicom.dataset
        :return:
        """
        if ds.Modality != 'PT': return 1.0
        if ds.Manufacturer != 'UIH': return 1.0
        try:
            # rescaleScople has been considering when converting to nifti1 format
            # doseCalibraFactor = float(ds.DoseCalibrationFactor)
            # rescaleSlope = float(ds.RescaleSlope)

            # read SUVbw tags from ds
            bw_factor = 1000.0
            decay_factor = 1.0
            acqDateTime = ds.AcquisitionDateTime
            patientWeight = float(ds.PatientWeight)
            radionuclide = ds.RadiopharmaceuticalInformationSequence[0]
            radionuclideHalfLife = float(radionuclide.RadionuclideHalfLife)
            radionuclideTotalDose = float(radionuclide.RadionuclideTotalDose)
            radionuclideStartDateTime = radionuclide.RadiopharmaceuticalStartDateTime
            # calculation of bw factor
            bw_factor = 1000.0 * patientWeight / radionuclideTotalDose
            # calculation of decay factor
            acq_datetime_0 = datetime.strptime(str(acqDateTime)[:14], '%Y%m%d%H%M%S')
            acq_datetime_1 = datetime.strptime(str(radionuclideStartDateTime)[:14], '%Y%m%d%H%M%S')
            delta_secs = acq_datetime_0 - acq_datetime_1
            decay_lambda = math.log(2) / radionuclideHalfLife
            decay_factor = math.exp(decay_lambda * delta_secs.total_seconds())
        except ZeroDivisionError as err:
            printMessage = 'Failed to read PET information for %s.'%(ds.PatientName)
            print(printMessage)
            logging.basicConfig(filename=self.log_file, level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
            logger=logging.getLogger(__name__)
            #logger.info( )
            logger.error(printMessage + '\n\t The specific error is: ' + str(err))
            return
        # correcting dose factor
        # dose_factor = rescaleSlope * doseCalibraFactor

        return decay_factor * bw_factor

    # ----------------------------------------------------------------------------------------
    #
    def _save_2_pet_suv_bqml(self,series_dicom_root, sub_root,
                             sub_name='sub-001',
                             func_name='pet',
                             task_name='rest'):
        # find udcm2bids tags and calc convert factor
        func_root = os.path.join(sub_root, func_name)
        bqml_nii_file = os.path.join(func_root,
                                     sub_name + '_task-' + task_name + '_PET-BQML.nii.gz')
        suvbw_nii_file = bqml_nii_file.replace('_PET-BQML', '_PET-SUVbw')
        suvbw_json_file = suvbw_nii_file.replace('.nii.gz', '.json')
        if os.path.exists(suvbw_nii_file): return
        suv_factor = []
        acqdatetime = []
        dicom_files = glob(os.path.join(series_dicom_root, '*.dcm'))
        for i, file in enumerate(dicom_files):
            ds = pydicom.read_file(file, stop_before_pixels=False)
            dt = str(ds.AcquisitionDateTime)[:14]
            if dt not in acqdatetime:
                acqdatetime.append(dt)
                suv_factor.append(self._calc_uih_pet_suvbw_factor(ds))
        # convert to bids
        if not os.path.isdir(func_root): os.mkdir(func_root)
        # check whether exist or not
        if not os.path.exists(bqml_nii_file):
            devnull = open(os.devnull, 'w')
            subprocess.call(['dcm2niix', '-b', 'y', '-z', 'y',
                             '-f', sub_name + '_task-' + task_name + '_PET-BQML',
                             '-o', func_root, series_dicom_root],
                            stdout=devnull, stderr=subprocess.STDOUT)
        # convert bqml to suv_bw with suv_factor
        nib_img_bqml = nib.load(bqml_nii_file)
        if len(suv_factor) > 1:
            nib_3d_imgs_bqml = nib.four_to_three(nib_img_bqml)
            np_3d_imgs_bqml = [nib_3d_img_bqml.get_data() for nib_3d_img_bqml in nib_3d_imgs_bqml]
            affines = [nib_3d_img_bqml.affine for nib_3d_img_bqml in nib_3d_imgs_bqml]
            np_3d_imgs_suvbw = [np_3d_img * c_factor
                                for np_3d_img, c_factor in zip(np_3d_imgs_bqml, suv_factor)]
            nib_3d_imgs_suvbw = [nib.Nifti1Image(new_np_3d_img, affine)
                                 for new_np_3d_img, affine in zip(np_3d_imgs_suvbw, affines)]
            nib_img_suvbw = nib.concat_images(nib_3d_imgs_suvbw)
            nib_img_suvbw.to_filename(suvbw_nii_file)
        else:
            nib_3d_img_bqml = nib_img_bqml
            np_3d_img_bqml = nib_3d_img_bqml.get_data()
            affine = nib_3d_img_bqml.affine
            np_3d_img_suvbw = np_3d_img_bqml * suv_factor[0]
            nib_3d_img_suvbw = nib.Nifti1Image(np_3d_img_suvbw, affine)
            nib_3d_img_suvbw.to_filename(suvbw_nii_file)
        with open(suvbw_json_file, 'wt', encoding='utf-8') as f_json:
            json.dump({'suvbw_factor': suv_factor,
                       'acquisition_time': acqdatetime},
                      f_json,
                      indent=4)
        return 

    # ----------------------------------------------------------------------------------------
    #
    def _save_2_generic(self,series_dicom_root, sub_root,
                        sub_name='sub-001',
                        func_name='func',
                        task_name='rest',
                        series_name='T1W'):
        # check whether exist
        func_root = os.path.join(sub_root, func_name)
        nii_file = os.path.join(func_root, sub_name + '_task-' + task_name + '_' + series_name + '.nii.gz')
        print(str(nii_file))
        if os.path.exists(nii_file): return 
        dicom_files = glob(os.path.join(series_dicom_root, '*.dcm'))
        # convert to bids
        if not os.path.isdir(func_root): os.mkdir(func_root)
        devnull = open(os.devnull, 'w')
        subprocess.call(['dcm2niix', '-b', 'y', '-z', 'y',
                         '-f', sub_name + '_task-' + task_name + '_' + series_name,
                         '-o', func_root, series_dicom_root],
                        stdout=devnull, stderr=subprocess.STDOUT)
        return 

    # -----------------------------------------------------------------------------------
    #
    def convert_uih_dcm_2_bids(self):
        """
        :param uih_dcm_root:
        :param fmri_pet_study_root:
        :param bids_func_info:      [{'series_description': 'epi_tra',
                                      'type': 'T1W' / 'BOLD' / 'DWI' / 'PET',
                                      'bids_func_name': 'anat',
                                      'bids_task_name': 'rest',
                                      'bids_session_name' : '01'}, ... ]

        :return:
        """
        uih_dcm_root = self.dicom_root
        fmri_pet_study_root = self.bids_root
        bids_func_info = self.bids_func_info
        # find the patient root defined as '*_*_*' - UIH specific exported dicom pattern
        #patient_roots = list(set([os.path.dirname(bids_func_info[i]['08_SeriesRoot'])
        #                          for i in range(len(bids_func_info))]))
        i = 0
        for bids_func in bids_func_info:
        #for patient_root in patient_roots:
            # create sub bids folders
            patient_root = os.path.dirname(bids_func['08_SeriesRoot'])
            patient_name = basename(patient_root)
            sub_name = 'sub-' + str(patient_name.split('_')[1])
            sub_root = os.path.join(fmri_pet_study_root, sub_name)
            if not os.path.exists(sub_root): os.mkdir(sub_root)
            series_description = bids_func.get('08_SeriesRoot') #os.listdir(patient_root)
            #i = 0
                #for series_description in series_descriptions:
            #if not bids_func.get('05_SeriesDescription') in series_description: continue
            print('working on %s - %s' % (sub_name, series_description))
            try:
                dyn_sub_name = sub_name
                dyn_sub_name + '-{:02d}'.format(i)
                series_dicom_root = os.path.join(patient_root, series_description)
                if bids_func.get('10_Type') != 'PET' and bids_func.get('10_Type') != 'PT':
                    self._save_2_generic(series_dicom_root, sub_root, dyn_sub_name,
                                    func_name=str(bids_func.get('11_Func')),
                                    task_name=str(bids_func.get('12_Task')),
                                    series_name=str(bids_func.get('05_SeriesDescription')))
                else:
                    self._save_2_pet_suv_bqml(series_dicom_root, sub_root, dyn_sub_name,
                                         func_name=bids_func.get('11_Func'),
                                         task_name=bids_func.get('12_Task'))
                i += 1
            except:
                print('failed to convert %s - %s' % (sub_name, series_description))
        return 
