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

    # Create nodes from code lines
    def preprocess_lines(self, lines, source='inline'):
        for l,line in enumerate(lines):
            self.nodes.append(PPML_Node(
                code = line,
                line = l+1,
                source = source,
            ))

    # Group block lines
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

    # Replace specific symbols with substitution marks
    def preprocess_symbols(self):
        # Add replacement marks
        # TODO: we need to also properly treate arrays like this ["d#", "b"]
        replace = ["\\'", '\\"', "\n"]
        for n,node in enumerate(self.nodes):
            for i,symbol in enumerate(replace):
                self.nodes[n].code = self.nodes[n].code.replace(symbol,f"$@{i:02d}")

    # Preprocess options
    def preprocess_options(self):
        nodes = []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if node.code[:1]=='=':
                nodes[-1].options.append(node.code)
            else:
                nodes.append(node)
        self.nodes = nodes
    
    # Convert symbols to original letters
    def _postprocess_symbols(self, value):
        replace = ["\'", '\"', "\n"]
        if isinstance(value, (list, np.ndarray)):
            value = [self._postprocess_symbols(v) for v in value]
        else:
            for i,symbol in enumerate(replace):
                value = value.replace(f"$@{i:02d}", symbol)
        return value
    def postprocess_symbols(self):
        # Remove replacement marks
        for n,node in enumerate(self.nodes):
            if not isinstance(node,PPML_Node_String):
                continue
            self.nodes[n].value = self._postprocess_symbols(self.nodes[n].value)
            self.nodes[n].code = self._postprocess_symbols(self.nodes[n].code)
            
    # Group comment lines
    def postprocess_comments(self):
        # Group following comments
        nodes = [self.nodes.pop(0)]
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if nodes[-1].dtname=='empty':
                nodes.append(node)
            elif nodes[-1].indent<node.indent and node.dtname=='comment':
                nodes[-1].comments = nodes[-1].comments + node.comments
            else:
                nodes.append(node)
        self.nodes = nodes
        # Group preceeding comments
        nodes = [self.nodes.pop(-1)]
        while len(self.nodes)>0:
            node = self.nodes.pop(-1)
            if nodes[-1].dtname=='empty':
                nodes.append(node)
            elif nodes[-1].indent==node.indent and node.dtname=='comment':
                nodes[-1].comments = node.comments + nodes[-1].comments
            else:
                nodes.append(node)            
        self.nodes = list(reversed(nodes))
        # Flatten comments lists
        for n,node in enumerate(self.nodes):
            self.nodes[n].comments = "\n".join(node.comments)
            
    # Parse a code line
    def parse(self, ppml):
        self.preprocess_lines(ppml.split('\n'))
        self.preprocess_blocks()
        self.preprocess_symbols()
        self.preprocess_options()
        for n,node in enumerate(self.nodes):
                node = node.process_code()
                if node:
                    self.nodes[n] = node
        self.postprocess_symbols()
        self.postprocess_comments()
        for node in self.nodes:
            print(node.dtname,'|',node.name,'|',repr(node.value),
                  '|',repr(node.comments)) #,
            #      '|',repr(node.code))
        return True
