import numpy as np
import re
import os
from typing import List

from DPML_Node import *
from DPML_Converter import *

class ParseDPML:
    lines: str
    nodes: List = []
    
    def __init__(self, code, **kwargs):
        self.lines = code.split('\n')
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        pass

    def open(self, file_name):
        pass
        
    # Create nodes from code lines
    def pre_nodes(self, source='inline'):
        for l,line in enumerate(self.lines):
            self.nodes.append(DPML_Node(
                code = line,
                line = l+1,
                source = source,
            ))

    # Group block lines
    def pre_blocks(self):
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
    def pre_symbols(self):
        # Add replacement marks
        # TODO: we need to also properly treate arrays like this ["d#", "b"]
        replace = ["\\'", '\\"', "\n"]
        for n,node in enumerate(self.nodes):
            for i,symbol in enumerate(replace):
                self.nodes[n].code = self.nodes[n].code.replace(symbol,f"$@{i:02d}")
                
    # Convert symbols to original letters
    def _post_symbols(self, value):
        replace = ["\'", '\"', "\n"]
        if isinstance(value, (list, np.ndarray)):
            value = [self._post_symbols(v) for v in value]
        elif value is None:
            return value
        else:
            for i,symbol in enumerate(replace):
                value = value.replace(f"$@{i:02d}", symbol)
        return value
    def post_symbols(self):
        # Remove replacement marks
        for n,node in enumerate(self.nodes):
            self.nodes[n].value_raw = self._post_symbols(node.value_raw)
            self.nodes[n].code = self._post_symbols(node.code)
        
    # Group comment lines
    def post_comments(self):
        # Group following comments
        nodes = [self.nodes.pop(0)]
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if nodes[-1].keyword=='empty':
                nodes.append(node)
            elif nodes[-1].indent<node.indent and node.keyword=='comment':
                nodes[-1].comments = nodes[-1].comments + node.comments
            else:
                nodes.append(node)
        self.nodes = nodes
        # Group preceeding comments
        nodes = [self.nodes.pop(-1)]
        while len(self.nodes)>0:
            node = self.nodes.pop(-1)
            if nodes[-1].keyword=='empty':
                nodes.append(node)
            elif nodes[-1].indent==node.indent and node.keyword=='comment':
                nodes[-1].comments = node.comments + nodes[-1].comments
            else:
                nodes.append(node)            
        self.nodes = list(reversed(nodes))
        # Flatten comments lists
        for n,node in enumerate(self.nodes):
            self.nodes[n].comments = "\n".join(node.comments)

    # Assign options to preceeding nodes
    def post_options(self):
        # Collect options to correpsonding nodes
        nodes = [self.nodes.pop(0)]
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if node.keyword=='option':
                if nodes[-1].options is not None:
                    nodes[-1].options.append( node )
                else:
                    raise Exception(f"Node '{nodes[-1].keyword}' does not support options")
            else:
                nodes.append(node)
        self.nodes = nodes

    # Expand nodes that have a spetial feature
    def post_parse_types(self):
        nodes = []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            parsed = node.parse()
            if parsed:
                for node in parsed:
                    nodes.append(node)
            else:
                nodes.append(node)
        self.nodes = nodes
                
    # Remove empty nodes and lonely comments
    def post_remove(self):
        nodes = []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if node.keyword not in ['empty','comment']:
                nodes.append(node)
        self.nodes = nodes

    # Change node names according to node hierarchy
    def post_hierarchy(self):
        indent, names = [-1], []
        for node in self.nodes:
            if node.name is None:
                continue
            while node.indent<=indent[-1]:
                indent.pop()
                names.pop()                    
            names = names+[node.name]
            indent = indent+[node.indent]
            node.name = ".".join(names)
        # remove group nodes
        nodes = []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if node.keyword == 'group':
                continue
            nodes.append(node)
        self.nodes = nodes

    # Add modifications to nodes
    def post_modify(self):
        nodes = {}
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if node.name in nodes:
                nodes[node.name].mods.append( node )
            else:    
                nodes[node.name] = node
        self.nodes = nodes

    # Process values
    def _post_cast(self, src, node):
        value = src.value if src.value else src.value_raw
        if np.isscalar(value) and value in [None,'none','None']:
            # validate none values
            if node.defined:
                raise Exception(f"Value of node '{node.name}' must be defined")
            else:
                value = None
        elif node.dimension:
            # cast multidimensional values
            if isinstance(value, str):
                value = np.array(json.loads(value), dtype=node.dtype)
            else:
                value = np.array(value, dtype=node.dtype)
            # check if dimensions are correct
            for d,dim in enumerate(node.dimension):
                shape = value.shape[d]
                if dim[0] is not None and shape < dim[0]:
                    raise Exception(f"Node '{node.name}' has invalid dimension: dim({d})={shape} < {dim[0]}")
                if dim[1] is not None and shape > dim[1]:
                    raise Exception(f"Node '{node.name}' has invalid dimension: dim({d})={shape} > {dim[1]}")
        else:
            # cast scalar values
            if value is not None:
                value = node.dtype(value)
        return value
    def post_values(self):
        for key,node in self.nodes.items():
            # cast definition value
            node.value = self._post_cast(node, node)
            # cast modifications
            if node.mods:
                for mod in node.mods:
                    value = self._post_cast(mod, node)
                    if mod.keyword!='mod' and  mod.dtype!=node.dtype:
                        raise Exception(f"Datatype {node.dtype} of node '{node.name}' cannot be changed to {mod.dtype}")
                    # convert mod units to node units if necessary
                    if node.units and mod.units and node.units!=mod.units:
                        with DPML_Converter() as p:
                            value = p.convert(value, mod.units, node.units)
                    node.value = value
            # parse options
            if node.options:
                options = [] if node.defined else [None]
                # cast options
                for option in node.options:
                    option.value = self._post_cast(option, node)
                    options.append(option.value)
                # check if node value is in options
                if node.value not in options:
                    raise Exception(f"Value '{node.value}' of node '{node.name}' doesn't match with any option:",options)

    # Prepare raw nodes
    def initialize(self):
        self.pre_nodes()                     # determine nodes from lines
        self.pre_blocks()                    # combine text blocks
        self.pre_symbols()                   # encode text symbols
        for n,node in enumerate(self.nodes):
                node = node.parse()          # process code
                if node:
                    self.nodes[n] = node
        self.post_symbols()                  # decode text symbols
        self.post_comments()                 # combine comments
        self.post_options()                  # collect options
        self.post_remove()                   # remove empty nodes
        self.post_parse_types()              # parse special node types

    # Finalize all nodes
    def finalize(self):
        self.post_hierarchy()                # set hierarchycal naming
        self.post_modify()                   # modify node values
        self.post_values()                   # validate node values              
        
    # Display final nodes
    def display(self):
        for node in self.nodes.values():
            print(node.name,'|',node.indent,'|',node.keyword,'|',repr(node.value),
                  '|',repr(node.comments),
                  '|',repr(node.units), end='')
            if hasattr(node,'options'):
                if node.options:
                    print(' |',[o.value for o in node.options], end='')
            print()

    # Produce final data structure
    def data(self):
        data = {}
        for name,node in self.nodes.items():
            data[name] = node.value
        return data
