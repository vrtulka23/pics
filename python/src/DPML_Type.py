from typing import List
from pydantic import BaseModel
import numpy as np
import json
import csv

from DPML_Parser import *
import DPML

class DPML_Type(BaseModel):
    code: str 
    line: int
    source: str
    keyword: str
    
    dtype = str
    indent: int = 0
    name: str = None
    value: str = None
    value_raw: str = None
    isimport: bool = False
    defined: bool = False
    units: str = None
    dimension: List[tuple] = None
    options: List[BaseModel] = None
    
    def __init__(self, parser):
        kwargs = {}
        kwargs['line'] = parser.line
        kwargs['source'] = parser.source
        kwargs['indent'] = parser.indent
        kwargs['code'] = parser.code
        kwargs['name'] = parser.name
        kwargs['isimport'] = parser.isimport
        kwargs['value_raw'] = parser.value
        kwargs['units'] = parser.units
        kwargs['dimension'] = parser.dimension
        kwargs['defined'] = parser.defined
        if parser.keyword:
            kwargs['keyword'] = parser.keyword
        super().__init__(**kwargs)

    def parse(self, nodes):
        return False

    # Cast (raw-)value as a datatype self, or another node
    def cast_value(self, node=None):
        if node is None:
            node = self
        value = self.value if self.value else self.value_raw
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

    # Set value using value_raw or arbitrary value
    def set_value(self, value=None):
        if value is None:
            self.value = self.cast_value()
        else:
            self.value = value
        # parse options
        if self.options:
            # check if node value is in options
            if self.value not in self.options:
                raise Exception(f"Value '{self.value}' of node '{self.name}' doesn't match with any option:", self.options)
        return True

    # Modify value taking value of a different node
    def modify_value(self, node):
        value = node.cast_value(self)
        if node.keyword!='mod' and node.dtype!=self.dtype:
            raise Exception(f"Datatype {self.dtype} of node '{self.name}' cannot be changed to {node.dtype}")
        # convert mod units to node units if necessary
        if self.units and node.units and self.units!=node.units:
            with DPML_Converter() as p:
                value = p.convert(value, node.units, self.units)
        self.set_value(value)

    # Set option using value of a different node
    def set_option(self, node):
        if self.options is not None:
            if not self.defined and None not in self.options:
                self.options.append( None )
            optval = node.cast_value(self)
            if node.units and self.units and node.units!=self.units:
                with DPML_Converter() as p:
                    optval = p.convert(optval, node.units, self.units)
            self.options.append( optval )
        else:
            raise Exception(f"Node '{self.keyword}' does not support options")
        
class DPML_Type_Empty(DPML_Type):
    keyword: str = 'empty'

class DPML_Type_Group(DPML_Type):
    keyword: str = 'group'

class DPML_Type_Comment(DPML_Type):
    keyword: str = 'comment'

class DPML_Type_Option(DPML_Type):
    keyword: str = 'option'
    
class DPML_Type_Mod(DPML_Type):
    keyword: str = 'mod'

    def parse(self, nodes):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes)
                p.fill(self, self.value_raw)
        return None    

class DPML_Type_Boolean(DPML_Type):
    keyword: str = 'bool'
    value: bool = None
    dtype = bool

    def parse(self, nodes):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes)
                p.fill(self, self.value_raw)
        return None    
    
class DPML_Type_Integer(DPML_Type):
    keyword: str = 'int'
    value: int = None
    options: List[BaseModel] = []
    dtype = int

    def parse(self, nodes):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes)
                p.fill(self, self.value_raw)
        return None    
    
class DPML_Type_Float(DPML_Type):
    keyword: str = 'float'
    value: float = None
    options: List[BaseModel] = []
    dtype = float

    def parse(self, nodes):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes)
                p.fill(self, self.value_raw)
        return None    
    
class DPML_Type_String(DPML_Type):
    keyword: str = 'str'
    options: List[BaseModel] = []

    def parse(self, nodes):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes)
                p.fill(self, self.value_raw)
        return None    

class DPML_Type_Condition(DPML_Type):
    keyword: str = 'condition'

    def parse(self, nodes):
        # Solve condition
        if self.name.endswith('@case'):
            with DPML.DPML() as p:
                p.use(nodes)
                self.value = p.expression(self.value_raw)
        return None
    
class DPML_Type_Import(DPML_Type):
    keyword: str = 'import'

    def parse(self, nodes):
        # Parse import code
        nodes_new = []
        with DPML.DPML() as p:
            p.use(nodes)
            for node in p.request(self.value_raw):
                path = self.name.split('.{')
                path.pop()
                path.append(node.name)                
                node.source = self.source
                node.line = self.line
                node.name = ".".join(path)
                node.indent = self.indent
                nodes_new.append(node)
        return nodes_new

class DPML_Type_Table(DPML_Type):
    keyword: str = 'table'
    
    def parse(self, nodes):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes)
                p.fill(self,self.value_raw)
        lines = self.value_raw.split("\n")
        # Parse nodes from table header
        table = []
        while len(lines)>0:
            line = lines.pop(0)
            if line.strip()=='':
                break
            # Parse node parameters
            parser = DPML_Parser(
                code=line,
                line=self.line,
                source=self.source
            )
            parser.get_name()      # parse node name
            parser.get_type()      # parse node type
            parser.get_units()     # parse node units
            if not parser.isempty():
                raise Exception(f"Incorrect header format: {line}")
            # Initialize actual node
            types = {
                'bool':  DPML_Type_Boolean,
                'int':   DPML_Type_Integer,
                'float': DPML_Type_Float,
                'str':   DPML_Type_String,
            }
            if parser.keyword in types:
                node = types[parser.keyword](parser)
                node.value = []
                table.append(node)
            else:
                raise Exception(f"Incorrect format or missing empty line after header: {self.code}")
        # Remove whitespaces from all table rows
        for l,line in enumerate(lines):
            lines[l] = line.strip()
            if line=='': del lines[l]
        # Read table and assign its values to the nodes
        ncols = len(table)
        csvtab = csv.reader(lines, delimiter=' ')
        for row in csvtab:
            if len(row)>ncols or len(row)<ncols:
                raise Exception(f"Number of header nodes does not match number of table columns: {ncols} != {len(row)}")
            for c in range(ncols):
                table[c].value.append(row[c])
        # set additional node parameters
        nodes_new = []
        for node in table:
            nvalues = len(node.value)
            node.dimension = [(nvalues,nvalues)]
            node.name = self.name+'.'+node.name
            node.indent = self.indent
            nodes_new.append(node)
        return nodes_new
