import numpy as np
import re
import os
from typing import List
from math import isclose

from DPML_Node import *
from DPML_Converter import *
from DPML_Parser import *
from DPML_Settings import *

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
            elif node.keyword in ['empty','group']:
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
            elif len(nodes)==0:
                raise Exception(f"Node was not found:", path)
            else:
                raise Exception(f"Path returned multiple nodes for a value import:", path)
        else:
            with open(path,'r') as f:
                node.value_raw = f.read()
        return node
    
    def _eval_node(self, expr):
        expr = expr.strip()
        if expr=='':
            return None
        flags = []
        if expr[0]=='~':
            flags.append('negate')
            expr = expr[1:]
        if expr[0]=='!':
            flags.append('defined')
            expr = expr[1:]
        # parse node from the code
        kwargs = {'code': expr, 'line':0, 'source': 'expression'}
        p = DPML_Parser(keyword='node',**kwargs)
        p.get_value(equal_sign=False)
        if p.isimport:   # import existing node
            nodes = self.request(p.value)
            if len(nodes)==1:
                if 'defined' in flags:
                    node = DPML_Type_Boolean(value_raw='true',value=True,**kwargs)
                else:
                    node = nodes[0]
            elif len(nodes)==0:
                if 'defined' in flags:
                    node = DPML_Type_Boolean(value_raw='false',value=False,**kwargs)
                else:
                    node = None
            else:
                raise Exception(f"Path returned multiple nodes for a value import:", path)
        elif p.value=='true':
            node = DPML_Type_Boolean(value_raw='true',value=True,**kwargs)
        elif p.value=='false':
            node = DPML_Type_Boolean(value_raw='false',value=False,**kwargs)
        else:            # create anonymous node
            p.get_units()
            node = DPML_Type(p)
            node.set_value()
        if 'negate' in flags:
            if node.keyword=='bool':
                node.value = not node.value
                node.value_raw = 'true' if node.value else 'false'
            else:
                raise Exception(f"Negated node is not boolean but:", node.keyword)
        return node
    def _eval_comparison(self, expr):
        # return immediatelly if expression is a boolean
        if isinstance(expr,(bool,np.bool_)):
            return expr
        expr = expr.strip()
        # list of comparison opperators
        comps = [
            # neglect python rounding errors using 'isclose' function
            ('==', lambda a,b: isclose(a, b, rel_tol=DPML_EQUAL_PRECISION)),  
            ('!=', lambda a,b: a!=b),
            ('>=', lambda a,b: (a>b)|isclose(a, b, rel_tol=DPML_EQUAL_PRECISION)),
            ('<=', lambda a,b: (a<b)|isclose(a, b, rel_tol=DPML_EQUAL_PRECISION)),
            ('>',  lambda a,b: a>b ),
            ('<',  lambda a,b: a<b ),
        ]
        # evaluate pair comparisions
        for sign,fn in comps:
            if sign not in expr:
                continue
            # parse left and right nodes
            left,right = expr.split(sign)
            left,right = self._eval_node(left),self._eval_node(right)
            if not left or not right:
                raise Exception("Couldn't find all requested nodes:", expr)
            # perform comparison
            if left.keyword=='node':            # if left node datatype is unknown
                left.set_value(left.cast_value(right))
                left.convert_units(right)
                right.set_value()
                return fn(left.value, right.value)
            elif right.keyword=='node':         # if right node datatype is unknown
                left.set_value()
                right.set_value(right.cast_value(left))
                right.convert_units(left)
                return fn(left.value, right.value)
            elif left.keyword==right.keyword:   # if both datatypes are known
                left.set_value()
                right.set_value()
                right.convert_units(left)
                return fn(left.value, right.value)                
            else:                               # throw error if both datatypes are unknown
                raise Exception("Invalid comparison:", expr)
        # evaluate single comparisons
        node = self._eval_node(expr)
        node.set_value()
        if node.keyword=='bool':
            return node.value
        else:
            raise Exception("Single node expression needs to be a boolean:", expr)
    def expression(self, expr):
        expr = expr.strip()
        # immediately return boolean values
        if isinstance(expr,(bool,np.bool_)):
            return expr
        # check if parenthesis are properly terminated
        elif expr.count('(')!=expr.count(')'):
            raise Exception('Unterminated parenthesis in expression:', expr)
        # evaluate logical && and || and parenthesis
        ors, ands, buff = [], [], ''
        while expr:
            sign, expr = expr[0], expr[1:]
            if sign=='(': # evaluate content of parenthesis separately
                p = 1
                while p>0 and expr:
                    sign, expr = expr[0], expr[1:]
                    if sign=='(':   p += 1
                    elif sign==')' and p==1: break
                    elif sign==')' and p>1: p -= 1
                    buff = buff + sign
                buff = self.expression(buff)   # evaluate in subroutine
                expr = expr.lstrip()
            elif expr and sign+expr[0]=='||':  # evaluate logical 'or' with priority
                expr = expr[1:]                # skip the second pipe
                if ands:                       # terminate openned 'and' clause
                    ands.append(buff)
                    buff = np.all([self._eval_comparison(a) for a in ands])
                    ands = []
                ors.append(buff)
                buff = ''
            elif expr and sign+expr[0]=='&&':  # evaluate logical 'and'
                expr = expr[1:]                # skip the second ampersend
                ands.append(buff)
                buff = ''
            elif sign in ['\n','\t']:          # remove special characters
                continue
            else:
                buff = buff + sign             # add character to a buffer
        if ands:                               # terminate last openned 'and' clause
            ands.append(buff)
            buff = np.all([self._eval_comparison(a) for a in ands])
        ors.append(buff)                       # terminate 'or' clause
        return np.any([self._eval_comparison(o) for o in ors])    
        
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
