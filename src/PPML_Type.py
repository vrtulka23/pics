from typing import List
from pydantic import BaseModel
import numpy as np
import json
import csv

from PPML_Parser import *

class PPML_Type(BaseModel):
    code: str 
    line: int
    source: str
    keyword: str
    
    dtype = str
    indent: int = 0
    name: str = None
    value: str = None
    defined: bool = False
    units: str = None
    comments: str = []
    dimension: List[tuple] = None
    options: List[BaseModel] = None
    mods: List[BaseModel] = []
    
    def __init__(self, parent):
        kwargs = {}
        kwargs['line'] = parent.line
        kwargs['source'] = parent.source
        kwargs['indent'] = parent.indent
        kwargs['code'] = parent.code
        kwargs['name'] = parent.name
        super().__init__(**kwargs)

    def parse(self):
        pass
        
class PPML_Type_Empty(PPML_Type):
    keyword: str = 'empty'

class PPML_Type_Mod(PPML_Type):
    keyword: str = 'mod'

class PPML_Type_Group(PPML_Type):
    keyword: str = 'group'

class PPML_Type_Comment(PPML_Type):
    keyword: str = 'comment'

class PPML_Type_Option(PPML_Type):
    keyword: str = 'option'
    
class PPML_Type_Boolean(PPML_Type):
    keyword: str = 'bool'
    value: bool = None
    dtype = bool
    
class PPML_Type_Integer(PPML_Type):
    keyword: str = 'int'
    value: int = None
    options: List[BaseModel] = []
    dtype = int

class PPML_Type_Float(PPML_Type):
    keyword: str = 'float'
    value: float = None
    options: List[BaseModel] = []
    dtype = float

class PPML_Type_String(PPML_Type):
    keyword: str = 'str'

class PPML_Type_Table(PPML_Parser, PPML_Type):
    node: PPML_Type = None
    keyword: str = 'table'
    ccode: str = None
    
    def _node_type(self):
        types = [
            PPML_Type_Boolean,
            PPML_Type_Integer,
            PPML_Type_Float,
            PPML_Type_String,
        ]
        for nd in types:
           node_try = nd(
               parent = self,
           )
           m=re.match('^(\s+'+node_try.keyword+')', self.ccode)
           if m:
               self.node = node_try
               self._strip(m.group(1))
               break
        if self.node is None:
            raise Exception(f"Type not recognized: {self.code}")
        
    def parse(self):
        name = self.name
        lines = self.value.split("\n")
        nodes = []
        while len(lines)>0:
            line = lines.pop(0)
            if line=='':
                break
            self.ccode = line
            self.code = line
            steps = [
                self._get_name,      # parse node name
                self._node_type,     # parse node type
                self._get_units,     # parse node units
            ]
            for step in steps:
                step()
            if self.node and self._isempty():
                self.node.name = name+'.'+self.node.name
                self.node.value = []
                nodes.append(self.node)
            else:
                raise Exception(f"Incorrect format or missing empty line after header: {self.code}")
        for l,line in enumerate(lines):
            lines[l] = line.strip()
        ncols = len(nodes)
        table = csv.reader(lines, delimiter=' ')
        for row in table:
            if len(row)>ncols or len(row)<ncols:
                raise Exception(f"Number of header nodes does not match number of table columns: {ncols} != {len(row)}")
            for c in range(ncols):
                nodes[c].value.append(row[c])
        for node in nodes:
            nvalues = len(node.value)
            node.dimension = [(nvalues,nvalues)]
            node.comments = ''
        return nodes
