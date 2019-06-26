#from nipype import Workflow, Node, MapNode, Function
import nipype.pipeline.engine as pe
from nipype.interfaces.io import SelectFiles, DataSink
from os.path import join
from mni import mni
from suvr import suv

def initiate_workflow(input_file_list, output_dir,opts):
    wf = pe.Workflow(name='pet-preprocessing-workflow',base_dir=join(output_dir,'preprocessing_output'))
    if opts.mni:
        mni_node = pe.Node(mni(input=input_file_list),name = 'mni')
    if opts.suvr:
        suvr_node = pe.Node(suv(input=input_file_list), name ='suvr')
    if opts.mni and opts.suvr:
        wf.connect(mni_node,'mni_file',suvr_node,'infile_suvr')

    #test condition
    wf.write_graph(join(output_dir,"workflow_graph.dot"))
    return wf

def run_workflow(wf):
    res = wf.run()
    return res
