import numpy as np
import re
import os
from typing import List

from PPML_Node import *
    
class ParsePPML:
    nodes: List = []
    
    def __init__(self,**kwargs):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        pass

    def open(self, file_name):
        pass

    def preprocess_lines(self, lines, source='inline'):
        for l,line in enumerate(lines):
            self.nodes.append(PPML_Node_Empty(
                code = line,
                line = l+1,
                source = source,
            ))

    def preprocess_blocks(self):
        nodes = []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if '"""' in node.code:
                block = []
                while len(self.nodes)>0:
                    subnode = self.nodes.pop(0)
                    if '"""' in subnode.code:
                        node.code += "\n".join(block) + subnode.code
                        break
                    else:
                        block.append( subnode.code )
                if len(self.nodes)==0:
                    raise Exception("Block structure starting on line %d is not properly terminated."%node['line'])
                nodes.append(node)
            else:
                nodes.append(node)
        self.nodes = nodes

    def preprocess_symbols(self):
        # Add replacement marks
        replace = ["\\'", '\\"', "\n"]
        for n,node in enumerate(self.nodes):
            for i,symbol in enumerate(replace):
                self.nodes[n].code = self.nodes[n].code.replace(symbol,f"$@{i:02d}")

    def postprocess_symbols(self):
        # Remove replacement marks
        replace = ["\'", '\"', "\n"]
        for i,symbol in enumerate(replace):
            results[1] = results[1].replace(f"$@{i:02d}", symbol)

    def parse(self, ppml):
        self.preprocess_lines(ppml.split('\n'))
        self.preprocess_blocks()
        self.preprocess_symbols()
        for n,node in enumerate(self.nodes):
            for nd in PPML_Nodes:
                ndtype = nd(**node.dict()).match()
                if ndtype:
                    self.nodes[n] = ndtype

        for node in self.nodes:
            print(node)
        return True
