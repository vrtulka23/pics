from typing import List
from pydantic import BaseModel
import numpy as np
import json
import csv

from DPML_Parser import *
from DPML_Settings import *
from DPML_Converter import *
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
    
    def __init__(self, parser=None, **kwargs):
        if parser:
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

    def parse(self, nodes, units):
        return False

    # Cast (raw-)value as a datatype self, or another node
    def cast_value(self, node=None):
        if node is None:
            node = self
        value = self.value if self.value is not None else self.value_raw
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
                # casting string as boolean returns true always if string is non-empty
                # that's why we need to convert it expicitely
                if node and node.keyword=='bool':
                    if value==KWD_TRUE:
                        value = True
                    elif value==KWD_FALSE:
                        value = False
                    elif not isinstance(value,(bool,np.bool_)):
                        raise Exception("Could not convert raw value to boolean type:",value)
                else:
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

    # Convert unit to units of another node
    def convert_units(self, node, units):
        if self.units and node.units and self.units!=node.units:
            with DPML_Converter(units) as p:
                self.value = p.convert(self.value, self.units, node.units)
                self.units = node.units        

    # Modify value taking value of a different node
    def modify_value(self, node, units):
        if node.keyword!='mod' and node.dtype!=self.dtype:
            raise Exception(f"Datatype {self.dtype} of node '{self.name}' cannot be changed to {node.dtype}")
        node.set_value(node.cast_value(self))
        node.convert_units(self, units)
        self.set_value(node.value)

    # Set option using value of a different node
    def set_option(self, node, units):
        if self.options is not None:
            if not self.defined and None not in self.options:
                self.options.append( None )
            node.set_value(node.cast_value(self))
            node.convert_units(self, units)
            self.options.append(node.value)
        else:
            raise Exception(f"Node '{self.keyword}' does not support options")

class DPML_Type_Empty(DPML_Type):
    keyword: str = 'empty'

class DPML_Type_Group(DPML_Type):
    keyword: str = 'group'

class DPML_Type_Option(DPML_Type):
    keyword: str = 'option'
    
class DPML_Type_Mod(DPML_Type):
    keyword: str = 'mod'

    def parse(self, nodes, units):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes, units)
                p.fill(self, self.value_raw)
        return None    

class DPML_Type_Boolean(DPML_Type):
    keyword: str = 'bool'
    value: bool = None
    dtype = bool

    def parse(self, nodes, units):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes, units)
                p.fill(self, self.value_raw)
        return None    
    
class DPML_Type_Integer(DPML_Type):
    keyword: str = 'int'
    value: int = None
    options: List[BaseModel] = []
    dtype = int

    def parse(self, nodes, units):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes, units)
                p.fill(self, self.value_raw)
        return None    
    
class DPML_Type_Float(DPML_Type):
    keyword: str = 'float'
    value: float = None
    options: List[BaseModel] = []
    dtype = float

    def parse(self, nodes, units):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes, units)
                p.fill(self, self.value_raw)
        return None    
    
class DPML_Type_String(DPML_Type):
    keyword: str = 'str'
    options: List[BaseModel] = []

    def parse(self, nodes, units):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes, units)
                p.fill(self, self.value_raw)
        return None    

class DPML_Type_Condition(DPML_Type):
    keyword: str = 'condition'

    def parse(self, nodes, units):
        # Solve condition
        if self.name.endswith(SGN_CASE + KWD_CASE):
            with DPML.DPML() as p:
                p.use(nodes, units)
                self.value = p.expression(self.value_raw)
        return None

class DPML_Type_Unit(DPML_Type):
    keyword: str = 'unit'

    def parse(self, nodes, units):
        parser = DPML_Parser(
            code=self.value_raw,
            line=self.line,
            source=self.source
        )
        parser.get_name(path=False) # parse name
        parser.get_value()          # parse value
        parser.get_units()          # parse unit
        with DPML_Converter(units) as conv:
            unit = conv.multiply(
                conv.expression(parser.units),
                conv.unit(parser.value)
            )
            unit.symbol = '['+parser.name+']'
            units.append(unit)
        return None
    
class DPML_Type_Import(DPML_Type):
    keyword: str = 'import'

    def parse(self, nodes, units):
        # Parse import code
        nodes_new = []
        with DPML.DPML() as p:
            p.use(nodes, units)
            for node in p.request(self.value_raw):
                path = self.name.split(SGN_SEPARATOR + '{')
                path.pop()
                path.append(node.name)                
                node.source = self.source
                node.line = self.line
                node.name = SGN_SEPARATOR.join(path)
                node.indent = self.indent
                nodes_new.append(node)
        return nodes_new

class DPML_Type_Table(DPML_Type):
    keyword: str = 'table'
    
    def parse(self, nodes, units):
        if self.isimport:
            with DPML.DPML() as p:
                p.use(nodes, units)
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
            node.name = self.name + SGN_SEPARATOR + node.name
            node.indent = self.indent
            nodes_new.append(node)
        return nodes_new
