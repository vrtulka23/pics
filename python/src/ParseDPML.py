import numpy as np
import re
import os
from typing import List

from DPML_Node import *
from DPML_Converter import *

class ParseDPML:
    lines: str
    nodes: List = []
    
    def __init__(self, code=None, **kwargs):
        if code:
            self.lines = code.split('\n')
        else:
            self.lines = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        pass

    def open(self, file_name):
        pass
        
    # Create nodes from code lines
    def create_nodes(self, source='inline'):
        for l,line in enumerate(self.lines):
            self.nodes.append(DPML_Node(
                code = line,
                line = l+1,
                source = source,
            ))

    # Group block lines
    def group_block_values(self):
        nodes = []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if '"""' in node.code:
                block = []
                while len(self.nodes)>0:
                    subnode = self.nodes.pop(0)
                    if '"""' in subnode.code:
                        node.code += "\n".join(block) + subnode.code.lstrip()
                        break
                    else:
                        block.append( subnode.code )
                if len(self.nodes)==0:
                    raise Exception("Block structure starting on line %d is not properly terminated."%node.line)
                nodes.append(node)
            else:
                nodes.append(node)
        self.nodes = nodes
        
    # Replace specific symbols with substitution marks
    def encode_symbols(self):
        # Add replacement marks
        # TODO: we need to also properly treate arrays like this ["d#", "b"]
        replace = ["\\'", '\\"', "\n"]
        for n,node in enumerate(self.nodes):
            for i,symbol in enumerate(replace):
                self.nodes[n].code = self.nodes[n].code.replace(symbol,f"$@{i:02d}")
                
    # Convert symbols to original letters
    def _decode_symbols(self, value):
        replace = ["\'", '\"', "\n"]
        if isinstance(value, (list, np.ndarray)):
            value = [self._decode_symbols(v) for v in value]
        elif value is None:
            return value
        else:
            for i,symbol in enumerate(replace):
                value = value.replace(f"$@{i:02d}", symbol)
        return value
    def decode_symbols(self):
        # Remove replacement marks
        for n,node in enumerate(self.nodes):
            self.nodes[n].value_raw = self._decode_symbols(node.value_raw)
            self.nodes[n].code = self._decode_symbols(node.code)
                    
    def parse_nodes(self):
        nodes = []
        cname, cnum = [''], [0]
        indents, parents = [-1], []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            # Perform specific node parsing
            parsed = node.parse(nodes)
            if parsed: 
                # Add nodes to the queue and continue
                self.nodes = parsed + self.nodes
                continue
            # Create hierarchical name
            if node.name is not None:
                 while node.indent<=indents[-1]:
                     indents.pop()
                     parents.pop()
                 parents.append(node.name)
                 indents.append(node.indent)
                 node.name = ".".join(parents)
            # Add nodes to the list
            if node.keyword=='option':        # Set node option
                nodes[-1].set_option(node)
            elif node.keyword in ['empty','comment','group']:
                continue
            elif node.keyword=='condition':   # Parse conditions
                casename = cname[-1]
                if node.name.endswith('@case'):
                    if casename+'case'!=node.name:   # register new case
                        cname.append(node.name[:-4])
                        cnum.append(0)                                        
                    if node.value or cnum[-1]==1:
                        cnum[-1] += 1
                elif node.name==casename+'else':
                    cnum[-1] += 1
                elif node.name==casename+'end':
                    cname.pop()
                    cnum.pop()
                else:
                    raise Exception(f"Invalid condition:", node.name)
            else:
                # If part of a condition we need to do some extra steps
                if cname[-1]:
                    if cnum[-1]>1: # ignoring multiple valid cases
                        continue    
                    if not node.name.startswith(cname[-1]): # ending case
                        cname.pop()
                        cnum.pop()
                    node.name = node.name.replace('@case.','')
                    node.name = node.name.replace('@else.','')
                # Set the node value
                node.set_value()
                # If node was previously defined, modify its value
                for n in range(len(nodes)):
                    if nodes[n].name==node.name:
                        nodes[n].modify_value(node)
                        break
                # If node wasn't defined, create a new node
                else:
                    if node.keyword=='mod':
                        raise Exception(f"Modifying undefined node:",node.name)
                    nodes.append(node)
        self.nodes = nodes
                    
    # Read DPML code from a file
    def load(self, filepath):
        with open(filepath,'r') as f:
            self.lines += f.read().split('\n')
    
    # Prepare raw nodes
    def initialize(self):
        self.create_nodes()                  # determine nodes from lines
        self.group_block_values()            # combine text blocks
        self.encode_symbols()                # encode text symbols
        for n,node in enumerate(self.nodes):
            node = node.parse()              # process code
            if node:
                self.nodes[n] = node
        self.decode_symbols()                # decode text symbols
        self.parse_nodes()                   # parse nodes during initialization

    # Finalize all nodes
    def finalize(self):
        nodes = {}
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            nodes[node.name] = node
        self.nodes = nodes

    def query(self, query):
        nodes = []
        if query=='*':
            return self.nodes
        elif query[-2:]=='.*':
            for node in self.nodes:
                if node.name.startswith(query[:-1]):
                    node = node.copy()
                    node.name = node.name[len(query[:-1]):]
                    nodes.append(node)
        else:
            for node in self.nodes:
                if node.name==query:
                    node = node.copy()
                    node.name = node.name.split('.')[-1]
                    nodes.append(node)
        if len(nodes)==0:
            raise Exception(f"Cannot find node '{query}'")
        return nodes        

    def expression(self, expression):   # solve condition expression
        if expression.strip()=='true':
            return True
        elif expression.strip()=='false':
            return False
        else:
            raise Exception(f"Invalid condition: {expression}")        
        
    # Display final nodes
    def display(self):
        for node in self.nodes.values():
            print(node.name,'|',node.indent,'|',node.keyword,'|',repr(node.value),
                  '|',repr(node.comments),
                  '|',repr(node.units), end='')
            if hasattr(node,'options'):
                if node.options:
                    print(' |',node.options, end='') #[o.value for o in node.options], end='')
            print()

    # Produce final data structure
    def data(self):
        data = {}
        for name,node in self.nodes.items():
            data[name] = node.value
        return data
