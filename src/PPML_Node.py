from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re
import json

from PPML_Type import *

class PPML_Node(BaseModel):

    node: PPML_Type = None
    code: str               # original code
    ccode: str              # processed code
    line: int
    source: str
    dtname: str = 'base'
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
    
    def _strip(self, text):
        self.ccode = self.ccode[len(text):]

    def _isempty(self):
        return self.ccode.strip()==''
        
    def _get_indent(self):
        m=re.match('^(\s*)',self.ccode)
        if m:
            self.indent = len(m.group(1))
            self._strip(m.group(1))
            
    def _get_name(self):
        m=re.match('^([a-zA-Z0-9_-]+)', self.ccode)
        if m:
            self.name = m.group(1)
            self._strip(m.group(1))
        else:
            raise Exception("Name has an invalid format: "+self.ccode)

    def _get_defined(self):
        if self.ccode[:1]=='!':
            self.defined = True
            self._strip('!')
            if self.node:
                self.node.defined = self.defined
        
    def _get_dimension(self):
        pattern = '^(\[([0-9:]+)\])'
        m=re.match(pattern, self.ccode)
        if m: self.dimension = []
        while m:
            if ":" not in m.group(2):
                self.dimension.append((int(m.group(2)),int(m.group(2))))
            else:
                dmin,dmax = m.group(2).split(':')
                self.dimension.append((
                    int(dmin) if dmin else None,
                    int(dmax) if dmax else None
                ))
            self._strip(m.group(1))
            m=re.match(pattern, self.ccode)
        if self.node:
            self.node.dimension = self.dimension
        
    def _get_value(self):
        m=re.match('^(\s*=\s*("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+)))', self.ccode)
        if m:
            # Reduce matches
            results = [x for x in m.groups()[1:] if x is not None]
            # Save value
            self.value = results[1]
            self._strip(m.group(1))
        if self.value is None:
            raise Exception("Value has to be set after equal sign")
        if self.node:
            if self.value in [None,'none','None']:
                if self.node.defined:
                    raise Exception(f"Value of node '{self.node.name}' must be defined")
                self.node.value = None
            elif self.node.dimension:
                self.node.value = np.array(json.loads(self.value), dtype=self.node.dtcast)
            else:
                self.node.value = self.node.dtcast(self.value)
        
    def _get_units(self):
        m=re.match('^(\s*([^\s#=]+))', self.ccode)
        if m:
            self.units = m.group(2)
            self._strip(m.group(1))
            if self.node:
                self.node.units = self.units
        
    def _get_comment(self):
        m=re.match('^(\s*#\s*(.*))$', self.ccode)
        if m:
            self.comment = m.group(2)
            self._strip(m.group(1))
            if self.node:
                self.node.comments.append( self.comment )

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
           m=re.match('^(\s+'+node_try.dtname+')', self.ccode)
           if m:
               self.node = node_try
               break
        if self.node is None:
            raise Exception(f"Type not recognized: {self.code}")
        self._strip(m.group(1))
        self._get_defined()
        self._get_dimension()
        self._get_value()
        self._get_units()
        self._get_comment()
    
    def process_code(self):
        self.ccode = self.code
        steps = [
            self._node_empty,    # parse empty line node
            self._get_indent,    # parse line indent
            self._node_comment,  # parse comment node
            self._node_option,   # parse option node
            self._get_name,      # parse node name
            self._node_group,    # parse group node
            self._node_mod,      # parse base node (modification)
            self._node_type,     # parse type node
        ]
        for step in steps:
            step()
            if self.node and self._isempty():
                return self.node
        raise Exception(f"Incorrect format: {self.code}")

