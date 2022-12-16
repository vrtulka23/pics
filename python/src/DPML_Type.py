from typing import List
from pydantic import BaseModel
import numpy as np
import json
import csv

from DPML_Parser import *
import ParseDPML

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
    defined: bool = False
    units: str = None
    comments: List[str] = []
    dimension: List[tuple] = None
    options: List[BaseModel] = None
    mods: List[BaseModel] = []
    
    def __init__(self, parser):
        kwargs = {}
        kwargs['line'] = parser.line
        kwargs['source'] = parser.source
        kwargs['indent'] = parser.indent
        kwargs['code'] = parser.code
        kwargs['name'] = parser.name
        if parser.value:
            kwargs['value_raw'] = parser.value
        if parser.units:
            kwargs['units'] = parser.units
        if parser.comment:
            kwargs['comments'] = [ parser.comment ]
        if parser.dimension:
            kwargs['dimension'] = parser.dimension
        if parser.defined:
            kwargs['defined'] = parser.defined
        super().__init__(**kwargs)

    def parse(self):
        pass
        
class DPML_Type_Empty(DPML_Type):
    keyword: str = 'empty'

class DPML_Type_Mod(DPML_Type):
    keyword: str = 'mod'

class DPML_Type_Group(DPML_Type):
    keyword: str = 'group'

class DPML_Type_Comment(DPML_Type):
    keyword: str = 'comment'

class DPML_Type_Option(DPML_Type):
    keyword: str = 'option'
    
class DPML_Type_Boolean(DPML_Type):
    keyword: str = 'bool'
    value: bool = None
    dtype = bool
    
class DPML_Type_Integer(DPML_Type):
    keyword: str = 'int'
    value: int = None
    options: List[BaseModel] = []
    dtype = int

class DPML_Type_Float(DPML_Type):
    keyword: str = 'float'
    value: float = None
    options: List[BaseModel] = []
    dtype = float

class DPML_Type_String(DPML_Type):
    keyword: str = 'str'
    options: List[BaseModel] = []

class DPML_Type_Import(DPML_Type):
    keyword: str = 'import'

    def parse(self):
        # Parse import code
        with ParseDPML.ParseDPML(self.value_raw) as p:
            p.initialize()
            # Add proper indent and hierarchy
            for node in p.nodes:
                node.source = self.source
                node.line = self.line
                if self.name and node.indent==0:
                    node.name = self.name+'.'+node.name
                node.indent = node.indent+self.indent
            return p.nodes

class DPML_Type_Injection(DPML_Type):
    keyword: str = 'injection'    
    
class DPML_Type_Table(DPML_Type):
    keyword: str = 'table'
    
    def parse(self):
        lines = self.value_raw.split("\n")
        # Parse nodes from table header
        nodes = []
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
                nodes.append(node)
            else:
                raise Exception(f"Incorrect format or missing empty line after header: {self.code}")
        # Remove whitespaces from all table rows
        for l,line in enumerate(lines):
            lines[l] = line.strip()
            if line=='': del lines[l]
        # Read table and assign its values to the nodes
        ncols = len(nodes)
        table = csv.reader(lines, delimiter=' ')
        for row in table:
            if len(row)>ncols or len(row)<ncols:
                raise Exception(f"Number of header nodes does not match number of table columns: {ncols} != {len(row)}")
            for c in range(ncols):
                nodes[c].value.append(row[c])
        # set additional node parameters
        for node in nodes:
            nvalues = len(node.value)
            node.dimension = [(nvalues,nvalues)]
            node.name = self.name+'.'+node.name
            node.comments = ''
            node.indent = self.indent
        return nodes
