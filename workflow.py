from nipype import Workflow, Node, MapNode, Function
import nipype.pipeline.engine as pe
from os.path import join
from mni import mni

def initiate_workflow(input_file_list, output_dir):

    mni_node = pe.Node(mni(input_file_list),name = 'mni')
    suvr_node = pe.Node(suvr(input_file_list),name = 'suvr')

    wf = pe.Workflow(name='pet-preprocessing-workflow',base_dir=join(output_dir,'preprocessing_output')
    wf.connect(mni_node,'mni_file',suvr_node,'infile_suvr')

    #test condition
    wf.write_graph(join(output_dir,"workflow_graph.dot"))
    return wf

def run_workflow(wf):
    res = wf.run()
    return res
