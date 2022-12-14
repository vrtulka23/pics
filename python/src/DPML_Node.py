from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re

from DPML_Type import *
from DPML_Parser import *
from DPML_Settings import *

class DPML_Node(BaseModel):
    code: str               
    line: int
    source: str
    
    parser: DPML_Parser = None
    node: DPML_Type = None
    
    def _node_type(self):
        self.parser.get_type()      # parse node type
        self.parser.get_defined()   # parse node defined
        self.parser.get_dimension() # parse node dimensions
        self.parser.get_value()     # parse node value
        self.parser.get_units()     # parse node units
        self.parser.get_comment()   # parse node comments
        types = {
            'bool':  DPML_Type_Boolean,
            'int':   DPML_Type_Integer,
            'float': DPML_Type_Float,
            'str':   DPML_Type_String,
            'table': DPML_Type_Table,
        }
        if self.parser.keyword in types:
            self.node = types[self.parser.keyword](self.parser)

    def _node_empty(self):
        if self.parser.isempty():
            self.node = DPML_Type_Empty(self.parser)

    def _node_comment(self):
        self.parser.get_comment()
        if self.parser.comment:
            self.node = DPML_Type_Empty(self.parser)

    def _node_import(self):
        m=re.match(r'^([a-zA-Z0-9_.-]*\s*){(.*)}', self.parser.ccode)
        if m:
            self.parser.keyword = 'import'
            if m.group(1):
                self.parser.get_name()
                self.parser.ccode = self.parser.ccode.lstrip()
            self.parser.get_import()
            self.parser.get_comment()
            self.node = DPML_Type_Import(self.parser)

    def _node_unit(self):
        m=re.match(
            r'^[a-zA-Z0-9_.-]*'+
            re.escape(SGN_UNIT)+KWD_UNIT, 
            self.parser.ccode
        )
        if m:
            self.parser.get_unit()
            self.parser.get_comment()
            self.node = DPML_Type_Unit(self.parser)

    def _node_option(self):
        m=re.match(r'^=\s*', self.parser.ccode)
        if m:           
            self.parser.get_value()
            self.parser.get_units()
            self.parser.get_comment()
            self.node = DPML_Type_Option(self.parser)

    def _node_condition(self):
        m=re.match(
            r'^[a-zA-Z0-9_.-]*'+
            SGN_CASE+'('+KWD_CASE+'|'+KWD_ELSE+'|'+KWD_END+')',
            self.parser.ccode
        )
        if m:
            self.parser.get_condition()
            self.parser.get_comment()
            self.node = DPML_Type_Condition(self.parser)
            
    def _node_group(self):
        self.parser.get_comment()
        if self.parser.isempty():
            self.node = DPML_Type_Group(self.parser)

    def _node_mod(self):       # Parse modification without type
        m=re.match(r'^\s*=\s*', self.parser.ccode)
        if m:
            self.parser.keyword = 'mod'
            self.parser.get_value()
            self.parser.get_units()
            self.parser.get_comment()
            self.node = DPML_Type_Mod(self.parser)
            
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
        
    def determine_type(self):
        # Add replacement marks
        # TODO: we need to also properly treate arrays like this ["d#", "b"]
        encode = ["\\'", '\\"', "\n"]
        for i,symbol in enumerate(encode):
            code = self.code.replace(symbol,f"$@{i:02d}")
            
        # Determine node type
        self.parser = DPML_Parser(
            code=code,
            line=self.line,
            source=self.source
        )
        steps = [
            self._node_empty,         # parse empty line node
            self.parser.get_indent,   # parse line indent
            self._node_import,        # parse import node
            self._node_unit,          # parse unit node
            self._node_comment,       # parse comment node
            self._node_option,        # parse option node
            self._node_condition,     # parse condition node
            self.parser.get_name,     # parse node name
            self._node_group,         # parse group node
            self._node_mod,           # parse modification node
            self._node_type,          # parse node type
        ]
        for step in steps:
            step()
            if self.node and self.parser.isempty():
                break
        else:
            raise Exception(f"Incorrect format: {self.code}")
        
        # Remove replacement marks
        self.node.value_raw = self._decode_symbols(self.node.value_raw)
        self.node.code = self._decode_symbols(self.node.code)

        # Return proper node type
        return self.node
