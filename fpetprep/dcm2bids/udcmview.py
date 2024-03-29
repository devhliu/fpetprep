#----------------------------------------------------------------------------------------
#
#   Project - udcm2bids
#   Description:
#       A python processing package to convert UIH DICOM into bids format
#   File Name:    udcmview.py
#   Purpose:
#       to convert UIH specific dicom storage into bids format
#   Author: hui.liu02@united-imaging.com
#   Created 2019-05-31
#----------------------------------------------------------------------------------------

import os
import re
import difflib
import pydicom
import shutil

import pandas as pd
from pandas import ExcelFile
from glob import glob
from pydicom.misc import is_dicom

def edit_xlsx(xlsx_file):
    """
    sphiniix
    """
    xls = ExcelFile(xlsx_file)
    df = xls.parse(xls.sheet_names[0])
    descrips = df['05_SeriesDescription'].to_list()
    func_list = []
    task_list = []
    for descrip in descrips:
        if descrip.find('t1') != -1:
            taskName = 't1'
            funcName = 'anat'
        if descrip.find('rest') != -1: taskName = 'rest'
        elif descrip.find('noise') != -1:taskName = 'noise'
        if descrip.find('dyn') != -1 and descrip.find('pet') != -1 :funcName = 'dynPET'
        elif descrip.find('pet') != -1: funcName = 'staticPET'
        if descrip.find('bold') != -1:funcName = 'func'
        func_list.append(funcName)
        task_list.append(taskName)
    df['11_Func'] = func_list
    df['12_Task'] = task_list
    df.to_excel(xlsx_file)
    return func_list, task_list

def dump_xlsx2dict(xlsx_file):
    xls = ExcelFile(xlsx_file)
    df = xls.parse(xls.sheet_names[0])
    dict = df.to_dict()
    dict2list = [{key: value[i] for key, value in dict.items()}
           for i in range(len(dict['01_PatientName']))]

    return dict2list


def dump_series2json(dcm_root, mode='one_per_dir', series_file_pattern='00000001.dcm'):
    """
    :param dcm_root:
    :param mode:        'one_per_dir'
    :param series_file_pattern:
    :return:
    """
    if not os.path.exists(dcm_root): return {}
    series = {'01_PatientName':[],
              '02_PatientID':[],
              '03_StudyDate':[],
              '04_AcquisitionDateTime':[],
              '05_SeriesDescription':[],
              '06_NumberofSlices':[],
              '07_Load':[],
              '08_SeriesRoot':[],
              '09_SeriesFiles':[],
              '10_Type':[],
              '11_Func':[],
              '12_Task':[]}
    for subdir, _, files in os.walk(dcm_root):
        if len(files) <= 0: continue
        print('working on %s' % (subdir))
        # find right patterned files
        #TODO: verify whether re_pattern is doing anything
        re_pattern = series_file_pattern.replace('*', '.*')
        r_files = []
        if mode != 'one_per_dir': r_files = files
        else:
            for file in files: r_files += re.findall(re_pattern, file)
            r_files.sort()
            r_files = [r_files[0]]
        # iterate all found files
        pnames = []
        pids = []
        stypes = []
        sdates = []
        sdecrps = []
        acqdatetimes = []
        subdirs = []
        slices = {}
        series_keys = []
        tasks = []
        funcs = []
        for file in r_files:
            dcm_file = os.path.join(subdir, file)
            if not is_dicom(dcm_file): continue
            ds = pydicom.read_file(dcm_file)
            if hasattr(ds,'Modality'): stype = str(ds.Modality)
            else: stype = 'NA'
            if hasattr(ds, 'AcquisitionDate'): acqdate = str(ds.AcquisitionDate)
            else: acqdate = 'NA'
            if hasattr(ds, 'AcquisitionTime'): acqtime = str(ds.AcquisitionTime)
            else: acqtime = 'NA'
            if hasattr(ds, 'PatientName'): pname = str(ds.PatientName)
            else: pname = 'NA'
            if hasattr(ds, 'PatientID'): pid = str(ds.PatientID)
            else: pid = 'NA'
            if hasattr(ds, 'StudyDate'): sdate = str(ds.StudyDate)
            else: sdate = 'NA'
            try: func = ds[0x0065,0x102b].value.split('\\')[1]
            except: func = 'NA'
            try: task = ds[0x0065,0x100c].value
            except: task = 'NA'
            if hasattr(ds, 'SeriesDescription'): sdecrp = str(ds.SeriesDescription)
            else: sdecrp = 'NA'
            series_key = str(sdecrp + subdir)
            if series_key not in series_keys:
                series_keys.append(series_key)
                slices[series_key] = []
                pnames.append(pname)
                pids.append(pid)
                sdates.append(sdate)
                sdecrps.append(sdecrp)
                acqdatetimes.append(acqdate + acqtime)
                subdirs.append(subdir)
                stypes.append(stype)
                funcs.append(func)
                tasks.append(task)
            slices[series_key].append(file)
        # append to series
        series['01_PatientName'] += pnames
        series['02_PatientID'] += pids
        series['03_StudyDate'] += sdates
        series['04_AcquisitionDateTime'] += acqdatetimes
        series['05_SeriesDescription'] += sdecrps
        series['07_Load'] += [False] * len(pnames)
        series['08_SeriesRoot'] += subdirs
        series['10_Type'] += stypes
        series['11_Func'] += funcs
        series['12_Task'] += tasks
        for series_key in series_keys:
            series['06_NumberofSlices'].append(len(slices[series_key]))
            series['09_SeriesFiles'].append(slices[series_key])
    return series


def dump_series2xlsx(dcm_root, xlsx_file, mode='one_per_dir', series_file_pattern='00000001.dcm'):
    """
    :param dcm_root:
    :param xlsx_file:
    :param mode:            'one_per_dir'
    :param series_file_pattern:
    :return:
    """
    series = dump_series2json(dcm_root, mode=mode, series_file_pattern=series_file_pattern)
    if os.path.exists(xlsx_file):
        df_0 = pd.read_excel(xlsx_file)
        df_1 = pd.DataFrame(series)
        df = pd.concat([df_0, df_1], axis=0, sort=True)
    else:
        df = pd.DataFrame(series)
    df.to_excel(xlsx_file)
    return df.to_dict()



def cp_series(xlsx_file, target_root):
    """
    :param xlsx_file:
    :param target_root:
    :return:
    """
    if not os.path.exists(xlsx_file): return
    if not os.path.exists(target_root): os.makedirs(target_root)
    tags = pd.read_excel(xlsx_file)
    patient_ids = tags['02_PatientID'].values
    for i, patient_id in enumerate(patient_ids):
        load = tags['07_Load'].values[i]
        if load == False: continue
        series_description = str(tags['05_SeriesDescription'].values[i])
        study_date = str(tags['03_StudyDate'].values[i])
        acqdatetime = str(tags['04_AcquisitionDateTime'].values[i])
        series_root_0 = str(tags['08_SeriesRoot'].values[i])
        series_files_strs = tags['09_SeriesFiles'].values[i]
        series_files_strs = series_files_strs.replace('\'', '')
        series_files_strs = series_files_strs.replace('[', '')
        series_files_strs = series_files_strs.replace(']', '')
        series_files_strs = series_files_strs.replace(' ', '')
        series_files = series_files_strs.split(',')
        series_root_1 = os.path.join(target_root, str(patient_id), study_date, acqdatetime + '_' + series_description)
        if not os.path.exists(series_root_1): os.makedirs(series_root_1)
        for file in series_files:
            filename = str(file)
            shutil.copyfile(os.path.join(series_root_0, filename), os.path.join(series_root_1, filename))
    return


def diff_dcm_files(dcm_file_0, dcm_file_1):
    """
    :param dcm_file_0:
    :param dcm_file_1:
    :return:
    """
    ds_0 = pydicom.read_file(dcm_file_0, force=True)
    ds_1 = pydicom.read_file(dcm_file_1, force=True)
    dss = tuple([ds_0, ds_1])
    rep = []
    for ds in dss:
        lines = str(ds).split("\n")
        lines = [line + "\n" for line in lines]  # add the newline to end
        rep.append(lines)
    diff = difflib.Differ()
    for line in diff.compare(rep[0], rep[1]):
        if line[0] != "?": print(line)
    return


# Test Purpose
'''if __name__ == '__main__':
    dcm_root = '\\\\dataserver02\\PET-MR02\\11. 场地数据\北京宣武医院\\fMRI_PET'
    xlsx_file = 'E:\\xuanwu.xlsx'
    patient_roots = glob(os.path.join(dcm_root, '2019*', '*', 'Image', '*_*'))
    patient_roots += glob(os.path.join(dcm_root, '2019*', '*', '*_*'))
    for patient_root in patient_roots:
        try:
            print('working on %s'%(patient_root))
            dump_series2xlsx(patient_root, xlsx_file, mode='multi_per_dir')
        except:
            print('failed in converting %s'%(patient_root))'''

