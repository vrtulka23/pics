from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re

from PPML_Type import *
from PPML_Parser import *

class PPML_Node(PPML_Parser, BaseModel):

    node: PPML_Type = None
    code: str               # original code
    ccode: str              # processed code
    line: int
    source: str
    keyword: str = 'base'
    indent: int = 0
    name: str = None
    comment: str = None
    units: str = None
    value: str = None
    dimension: List[tuple] = None
    defined: bool = False

    def __init__(self, **kwargs):
        kwargs['ccode'] = kwargs['code']
        super().__init__(**kwargs)
    
    def _node_type(self):
        types = [
            PPML_Type_Boolean,
            PPML_Type_Integer,
            PPML_Type_Float,
            PPML_Type_String,
            PPML_Type_Table,
        ]
        for nd in types:
           node_try = nd(
               parent = self,
           )
           m=re.match('^(\s+'+node_try.keyword+')', self.ccode)
           if m:
               self.node = node_try
               break
        if self.node is None:
            raise Exception(f"Type not recognized: {self.code}")
        self._strip(m.group(1))

    def _node_empty(self):
        if self._isempty():
            self.node = PPML_Type_Empty(self)

    def _node_comment(self):
        self._get_comment()
        if self.comment:
            self.node = PPML_Type_Comment(self)
            self.node.comments.append( self.comment )

    def _node_option(self):
        m=re.match('^=\s*', self.ccode)
        if m:           
            self.node = PPML_Type_Option(self)
            self._get_value()
            self._get_units()
            self._get_comment()
    
    def _node_group(self):
        if self._isempty():
            self.node = PPML_Type_Group(self)

    def _node_mod(self):       # Parse modification without type
        m=re.match('^\s*=\s*', self.ccode)
        if m:
            self.node = PPML_Type_Mod(self)
            self._get_value()
            self._get_comment()
            
    def parse_code(self):
        self.ccode = self.code
        steps = [
            self._node_empty,    # parse empty line node
            self._get_indent,    # parse line indent
            self._node_comment,  # parse comment node
            self._node_option,   # parse option node
            self._get_name,      # parse node name
            self._node_group,    # parse group node
            self._node_mod,      # parse base node (modification)
            self._node_type,      # parse node type
            self._get_defined,   # parse node defined
            self._get_dimension, # parse node dimensions
            self._get_value,     # parse node value
            self._get_units,     # parse node units
            self._get_comment,   # parse node comments
        ]
        for step in steps:
            step()
            if self.node and self._isempty():
                return self.node
        raise Exception(f"Incorrect format: {self.code}")
