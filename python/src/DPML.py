import numpy as np
import re
import os
from typing import List

from DPML_Node import *
from DPML_Converter import *
from DPML_Parser import *

class DPML:
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
        self.nodestmp = []
        cname, cnum = [''], [0]
        indents, parents = [-1], []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            # Perform specific node parsing
            parsed = node.parse(self.nodestmp)
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
                self.nodestmp[-1].set_option(node)
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
                for n in range(len(self.nodestmp)):
                    if self.nodestmp[n].name==node.name:
                        self.nodestmp[n].modify_value(node)
                        break
                # If node wasn't defined, create a new node
                else:
                    if node.keyword=='mod':
                        raise Exception(f"Modifying undefined node:",node.name)
                    self.nodestmp.append(node)
        self.nodes = self.nodestmp

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
        
    # Read DPML code from a file
    def load(self, filepath):
        with open(filepath,'r') as f:
            self.lines += f.read().split('\n')

    # Use specific nodes
    def use(self, nodes):
        self.nodes = nodes

    # Select local nodes according to a query
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
            raise Exception(f"Cannot find node:", query)
        return nodes        

    # Request nodes from a path
    def request(self, path):
        if '?' in path:
            filename,query = path.split('?')
        else:
            filename,query = path,'*'
        if filename:  # open external file and parse the values
            with DPML() as p:
                p.load(filename)
                p.initialize()
            return p.query(query)
        else:         # use values parsed in the current file
            if not self.nodes:
                raise Exception(f"Local nodes are not available for DPML import:", path)
            return self.query(query)

    # Fill node with value from a path
    def fill(self, node, path):
        if '?' in path:
            nodes = self.request(path)
            if len(nodes)==1:
                node.value_raw = nodes[0].value_raw
                if not node.units:
                    node.units = nodes[0].units
            else:
                raise Exception(f"Path returned multiple nodes for a value import:", path)
        else:
            with open(path,'r') as f:
                node.value_raw = f.read()
        return node
        
    # Evaluate node value expression
    def _eval_node(self, parts):
        code = parts[-1].strip()
        if code=='':
            parts.pop()
            return parts
        p = DPML_Parser(
            code=code,
            line=0,
            source='',
            keyword='node'
        )
        p.get_value(equal_sign=False)
        if p.isimport:
            # Parse import code
            if '?' in p.value:
                filename,query = p.value.split('?')
            else:
                filename,query = p.value,'*'
            with DPML() as pd:
                if filename:  # open external file and parse the values
                    pd.load(filename)
                    pd.initialize()
                else:         # use values parsed in the current file
                    pd.use(self.nodes)
                # Return iported nodes
                nodes = pd.query(query)    
            print(nodes[0])
        else:
            p.get_units()
            node = DPML_Type(p)
            print(node)
        return parts
    
    def _eval_expr(self, expr):
        parts = ['']
        while expr:
            if expr[:2] in ['==','!=','>=','<=','||','&&']:
                parts = self._eval_node(parts)
                parts.append(expr[:2])
                parts.append('')
                expr = expr[2:]                
            elif expr[0] in ['(',')','<','>','!']:
                parts = self._eval_node(parts)
                parts.append(expr[0])
                parts.append('')
                expr = expr[1:]
            else:
                parts[-1] += expr[0]
                expr = expr[1:]
        parts = self._eval_node(parts)
        parts = [p for p in parts if p != '']
        print(parts)
        
    def expression(self, expr):   # solve condition expression
        if expr.strip()=='true':
            return True
        elif expr.strip()=='false':
            return False
        else:
            return self._eval_expr(expr)
            #raise Exception(f"Invalid condition: {expr}")        
        
    # Display final nodes
    def display(self):
        for node in self.nodes:
            print(node.name,'|',node.indent,'|',node.keyword,'|',repr(node.value),
                  '|',repr(node.units), end='')
            if hasattr(node,'options'):
                if node.options:
                    print(' |',node.options, end='') #[o.value for o in node.options], end='')
            print()

    # Produce final data structure
    def data(self):
        data = {}
        for node in self.nodes:
            data[node.name] = node.value
        return data
