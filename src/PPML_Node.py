from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re

from PPML_Type import *
from PPML_Parser import *

class PPML_Node(BaseModel):
    code: str               
    line: int
    source: str
    
    parser: PPML_Parser = None
    node: PPML_Type = None
    
    def _node_type(self):
        self.parser.get_type()      # parse node type
        self.parser.get_defined()   # parse node defined
        self.parser.get_dimension() # parse node dimensions
        self.parser.get_value()     # parse node value
        self.parser.get_units()     # parse node units
        self.parser.get_comment()   # parse node comments
        types = {
            'bool':  PPML_Type_Boolean,
            'int':   PPML_Type_Integer,
            'float': PPML_Type_Float,
            'str':   PPML_Type_String,
            'table': PPML_Type_Table,
        }
        if self.parser.keyword in types:
            self.node = types[self.parser.keyword](self.parser)

    def _node_empty(self):
        if self.parser.isempty():
            self.node = PPML_Type_Empty(self.parser)

    def _node_comment(self):
        self.parser.get_comment()
        if self.parser.comment:
            self.node = PPML_Type_Comment(self.parser)

    def _node_import(self):
        m=re.match(r'^([a-zA-Z0-9_.-]*\s*){(.*)}', self.parser.ccode)
        if m:
            if m.group(1):
                self.parser.get_name()
                self.parser.ccode = self.parser.ccode.lstrip()
            self.parser.get_import()
            self.parser.get_comment()
            self.node = PPML_Type_Import(self.parser)

    def _node_option(self):
        m=re.match('^=\s*', self.parser.ccode)
        if m:           
            self.parser.get_value()
            self.parser.get_units()
            self.parser.get_comment()
            self.node = PPML_Type_Option(self.parser)
            
    def _node_group(self):
        self.parser.get_comment()
        if self.parser.isempty():
            self.node = PPML_Type_Group(self.parser)

    def _node_mod(self):       # Parse modification without type
        m=re.match('^\s*=\s*', self.parser.ccode)
        if m:
            self.parser.get_value()
            self.parser.get_units()
            self.parser.get_comment()
            self.node = PPML_Type_Mod(self.parser)
            
    def parse(self):
        self.parser = PPML_Parser(
            code=self.code,
            line=self.line,
            source=self.source
        )
        steps = [
            self._node_empty,         # parse empty line node
            self.parser.get_indent,   # parse line indent
            self._node_import,        # parse import node
            self._node_comment,       # parse comment node
            self._node_option,        # parse option node
            self.parser.get_name,     # parse node name
            self._node_group,         # parse group node
            self._node_mod,           # parse modification node
            self._node_type,          # parse node type
        ]
        for step in steps:
            step()
            if self.node and self.parser.isempty():
                return self.node
        raise Exception(f"Incorrect format: {self.code}")
