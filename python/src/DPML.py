import numpy as np
import re
import os
from typing import List
from math import isclose

from DPML_Node import *
from DPML_Parser import *
from DPML_Settings import *

class DPML:
    lines: str
    nodes: List = []
    units: List = []
    source: str = 'inline'
    
    def __init__(self, code=None, **kwargs):
        if code:
            self.lines = code.split('\n')
        else:
            self.lines = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        pass

    # Prepare raw nodes
    def initialize(self):
        # Convert code lines to nodes
        l = 0
        nodes = []
        cname, cnum = [''], [0]
        indents, parents = [-1], []
        while len(self.lines)>0:
            l, line = l+1, self.lines.pop(0)
            node = DPML_Node(
                code = line,
                line = l,
                source = self.source,
            )
            # Group block structures
            if '"""' in node.code:
                block = []
                while len(self.lines)>0:
                    l, subline = l+1, self.lines.pop(0)
                    if '"""' in subline:
                        node.code += "\n".join(block) + subline.lstrip()
                        break
                    else:
                        block.append( subline )
                else:
                    raise Exception("Block structure starting on line %d is not properly terminated."%node.line)
            node = node.determine_type()
            nodes.append(node)
        self.nodes = nodes
        # Parse nodes
        nodes, units = [], []
        while len(self.nodes)>0:
            node = self.nodes.pop(0)
            # Perform specific node parsing
            parsed = node.parse(nodes, units)
            if parsed: 
                # Add parsed nodes to the queue and continue
                self.nodes = parsed + self.nodes
                continue
            # Create hierarchical name
            if node.name is not None:
                 while node.indent<=indents[-1]:
                     indents.pop()
                     parents.pop()
                 parents.append(node.name)
                 indents.append(node.indent)
                 node.name = SGN_SEPARATOR.join(parents)
            # Add nodes to the list
            if node.keyword=='option':        # Set node option
                nodes[-1].set_option(node, units)
            elif node.keyword in ['empty','group','unit']:
                continue
            elif node.keyword=='condition':   # Parse conditions
                casename = cname[-1]
                if node.name.endswith(SGN_CASE + KWD_CASE):
                    if casename+KWD_CASE!=node.name:   # register new case
                        cname.append(node.name[:-4])
                        cnum.append(0)                                        
                    if node.value or cnum[-1]==1:
                        cnum[-1] += 1
                elif node.name==casename + KWD_ELSE:
                    cnum[-1] += 1
                elif node.name==casename + KWD_END:
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
                    node.name = node.name.replace(
                        SGN_CASE + KWD_CASE + SGN_SEPARATOR,''
                    )
                    node.name = node.name.replace(
                        SGN_CASE + KWD_ELSE + SGN_SEPARATOR,''
                    )
                # Set the node value
                node.set_value()
                # If node was previously defined, modify its value
                for n in range(len(nodes)):
                    if nodes[n].name==node.name:
                        nodes[n].modify_value(node, units)
                        break
                # If node wasn't defined, create a new node
                else:
                    if node.keyword=='mod':
                        raise Exception(f"Modifying undefined node:",node.name)
                    nodes.append(node)
        self.nodes = nodes
        self.units = units
        
    # Read DPML code from a file
    def load(self, filepath):
        self.source = filepath
        with open(filepath,'r') as f:
            self.lines += f.read().split('\n')

    # Use specific nodes and units
    def use(self, nodes, units):
        self.nodes = nodes
        self.units = units
        
    # Select local nodes according to a query
    def query(self, query):
        nodes = []
        if query==SGN_WILDCARD:
            return self.nodes
        elif query[-2:]==SGN_SEPARATOR + SGN_WILDCARD:
            for node in self.nodes:
                if node.name.startswith(query[:-1]):
                    node = node.copy()
                    node.name = node.name[len(query[:-1]):]
                    nodes.append(node)
        else:
            for node in self.nodes:
                if node.name==query:
                    node = node.copy()
                    node.name = node.name.split(SGN_SEPARATOR)[-1]
                    nodes.append(node)
        return nodes        

    # Request nodes from a path
    def request(self, path, count=None):
        if SGN_QUERY in path:
            filename,query = path.split(SGN_QUERY)
        else:
            filename,query = path,SGN_WILDCARD
        if filename:  # open external file and parse the values
            with DPML() as p:
                p.load(filename)
                p.initialize()
            nodes = p.query(query)
        else:         # use values parsed in the current file
            if not self.nodes:
                raise Exception(f"Local nodes are not available for DPML import:", path)
            nodes = self.query(query)
        if count:
            if isinstance(count, list) and len(nodes) not in count:
                raise Exception(f"Path returned invalid number of nodes:", path, count, len(nodes))
            elif np.isscalar(count) and len(nodes)!=count:
                raise Exception(f"Path returned invalid number of nodes:", path, count, len(nodes))
        return nodes

    # Fill node with value from a path
    def fill(self, node, path):
        if SGN_QUERY in path:
            nodes = self.request(path, count=1)
            node.value_raw = nodes[0].value_raw
            if not node.units:
                node.units = nodes[0].units
        else:
            with open(path,'r') as f:
                node.value_raw = f.read()
        return node
    
    def _eval_node(self, expr):
        expr = expr.strip()
        if expr=='':
            return None
        flags = []
        if expr[0]==SGN_NEGATE:
            flags.append('negate')
            expr = expr[1:]
        if expr[0]==SGN_DEFINED:
            flags.append('defined')
            expr = expr[1:]
        # parse node from the code
        kwargs = {'code': expr, 'line':0, 'source': 'expression'}
        p = DPML_Parser(keyword='node',**kwargs)
        p.get_value(equal_sign=False)
        if p.isimport:   # import existing node
            nodes = self.request(p.value, count=[0,1])
            if len(nodes)==1:
                if 'defined' in flags:
                    node = DPML_Type_Boolean(value_raw=KWD_TRUE,value=True,**kwargs)
                else:
                    node = nodes[0]
            elif len(nodes)==0:
                if 'defined' in flags:
                    node = DPML_Type_Boolean(value_raw=KWD_FALSE,value=False,**kwargs)
                else:
                    node = None
        elif p.value==KWD_TRUE:
            node = DPML_Type_Boolean(value_raw=KWD_TRUE,value=True,**kwargs)
        elif p.value==KWD_FALSE:
            node = DPML_Type_Boolean(value_raw=KWD_FALSE,value=False,**kwargs)
        else:            # create anonymous node
            p.get_units()
            node = DPML_Type(p)
            node.set_value()
        if 'negate' in flags:
            if node.keyword=='bool':
                node.value = not node.value
                node.value_raw = KWD_TRUE if node.value else KWD_FALSE
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
            ('==', lambda a,b: isclose(a, b, rel_tol=EQUAL_PRECISION)),  
            ('!=', lambda a,b: a!=b),
            ('>=', lambda a,b: (a>b)|isclose(a, b, rel_tol=EQUAL_PRECISION)),
            ('<=', lambda a,b: (a<b)|isclose(a, b, rel_tol=EQUAL_PRECISION)),
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
                left.convert_units(right, self.units)
                right.set_value()
                return fn(left.value, right.value)
            elif right.keyword=='node':         # if right node datatype is unknown
                left.set_value()
                right.set_value(right.cast_value(left))
                right.convert_units(left, self.units)
                return fn(left.value, right.value)
            elif left.keyword==right.keyword:   # if both datatypes are known
                left.set_value()
                right.set_value()
                right.convert_units(left, self.units)
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

    # Use node values to parse a template
    def template(self, template, output=None):
        if os.path.isfile(template): 
            with open(template,'r') as f:
                tpl = f.read()
        else:
            tpl = template
        out = ''
        kwargs = {'line':0, 'source': 'template', 'keyword':'tpl'}
        while len(tpl)>0:
            sign, tpl = tpl[0], tpl[1:]
            if sign=='{':
                p = DPML_Parser(code=tpl, **kwargs)
                p.get_import()
                p.get_format()
                if p.value and p.ccode[0]=='}':
                    nodes = self.request(p.value, count=1)
                    if p.formating:
                        form = "{0"+p.formating+"}"
                        out += form.format(nodes[0].value)
                    else:
                        out += str(nodes[0].value)
                    tpl = p.ccode[1:]
                else:
                    out += sign
            else:
                out += sign
        if output:
            with open(template,'r+') as f:
                f.write(out)
        return out
            
                
        
        
