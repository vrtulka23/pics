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
    def pre_lines(self, lines, source='inline'):
        for l,line in enumerate(lines):
            self.nodes.append(PPML_Node(
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
            self.nodes[n].value = self._post_symbols(node.value)
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
        """
        # Assign lonely comments to following sibling nodes
        nodes = [self.nodes.pop(0)]
        cnode = None
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if node.keyword=='comment':
                cnode = node
                continue
            elif node.keyword=='empty':
                continue
            elif cnode:
                if cnode.indent==node.indent:
                    node.comments =  cnode.comments + node.comments
                elif cnode.indent>node.indent:
                    cnode = None
            nodes.append(node)
        self.nodes = nodes
        """
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
            
    # Remove empty nodes and lonely comments
    def post_remove_empty(self):
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

    # Modify node values
    def post_modify(self):
        nodes = {}
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            if node.name in nodes:
                nodes[node.name].mods.append( node )
            else:    
                nodes[node.name] = node
        self.nodes = nodes

    # Validate node values
    def _post_cast(self, value, dtype, dimension):
        if dimension:
            if isinstance(value, str):
                return np.array(json.loads(value), dtype=dtype)
            else:
                return np.array(value, dtype=dtype)
        else:
            return dtype(value)
    def post_values(self):
        for key,node in self.nodes.items():
            if np.isscalar(node.value) and node.value in [None,'none','None']:
                if node.defined:
                    raise Exception(f"Value of node '{self.name}' must be defined")
                else:
                    node.value = None
            else:
                node.value = self._post_cast(node.value, node.dtype, node.dimension)
            if node.options:
                options = [] if node.defined else [None]
                for option in node.options:
                    option.value = self._post_cast(option.value, node.dtype, node.dimension)
                    options.append(option.value)
                if node.value not in options:
                    raise Exception(f"Value '{node.value}' of node '{node.name}' doesn't match with any option:",options)

    # Parse a code line
    def parse(self, ppml):
        self.pre_lines(ppml.split('\n'))     # determine nodes from lines
        self.pre_blocks()                    # combine text blocks
        self.pre_symbols()                   # encode text symbols
        for n,node in enumerate(self.nodes):
                node = node.parse_code()   # process code
                if node:
                    self.nodes[n] = node
        self.post_symbols()                  # decode text symbols
        self.post_comments()                 # combine comments
        self.post_options()                  # collect options
        self.post_remove_empty()             # remove empty nodes
        self.post_hierarchy()                # set hierarchycal naming
        self.post_modify()                   # modify node values
        self.post_values()                   # validate node values              
        for node in self.nodes.values():
            print(node.name,'|',node.indent,'|',node.keyword,'|',repr(node.value),
                  '|',repr(node.comments),
                  '|',repr(node.units), end='')
            if hasattr(node,'options'):
                if node.options:
                    print(' |',[o.value for o in node.options], end='')
            print()
        return True
