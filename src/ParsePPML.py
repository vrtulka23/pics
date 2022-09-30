import numpy as np
import re
import os

from PPML_Node import *
    
class ParsePPML:
   
    def __init__(self,**kwargs):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        pass

    def open(self, file_name):
        pass

    def parse_lines(self, lines, file_name=None):
        nodes = []
        for l,line in enumerate(lines):
            nodes.append(dict(
                code = line,
                line = l+1,
            ))
        return nodes

    def parse_blocks(self, nodes):
        nodes_new = []
        while len(nodes)>0:
            node = nodes.pop(0)
            if '"""' in node['code']:
                block = []
                while len(nodes)>0:
                    subnode = nodes.pop(0)
                    if '"""' in subnode['code']:
                        node['code'] += "\n".join(block) + subnode['code']
                        break
                    else:
                        block.append( subnode['code'] )
                if len(nodes)==0:
                    raise Exception("Block structure starting on line %d is not properly terminated."%node['line'])
                nodes_new.append(node)
            else:
                nodes_new.append(node)
        return nodes_new
        
    def parse(self, ppml):
        nodes = self.parse_lines(ppml.split('\n'))
        nodes = self.parse_blocks(nodes)
        for node in nodes:
            for nd in PPML_Nodes:
                datatype = nd().match(node['code'])
                if datatype:
                    print(datatype)

        return True
