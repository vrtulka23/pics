from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re
import json

class PPML_Node(BaseModel):
    code: str 
    line: int
    source: str
    dtname: str
    indent: int = 0
    name: str = None
    comments: List[str] = []

    value: int = None
    defined: bool = False
    dimension: List[tuple] = None
    units: str = None

    def __init__(self, **kwargs):
        if 'parent' in kwargs:
            parent = kwargs['parent']
            del kwargs['parent']
            kwargs['line'] = parent.line
            kwargs['source'] = parent.source
            kwargs['indent'] = parent.indent
        super().__init__(**kwargs)

class PPML(BaseModel):

    node: PPML_Node = None
    code: str               # original code
    ccode: str              # processed code
    line: int
    source: str
    dtname: str = 'base'
    indent: int = 0
    name: str = None
    comment: str = None
    units: str = None

    def __init__(self, **kwargs):
        kwargs['ccode'] = kwargs['code']
        super().__init__(**kwargs)
    
    def _strip(self, text):
        self.ccode = self.ccode[len(text):].lstrip()

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

    def _get_units(self, node=False):
        m=re.match('^([^\s#=]+)', self.ccode)
        if m:
            self.units = m.group(1)
            self._strip(m.group(1))
            if node:
                self.node.units = self.units
        
    def _get_comment(self, node=False):
        m=re.match('^(#\s*(.*))$', self.ccode)
        if m:
            self.comment = m.group(2)
            self._strip(m.group(1))
            if node:
                self.node.comments.append( self.comment )

    def _node_empty(self):
        if self._isempty():
            self.node = PPML_Node_Empty(
                parent = self,
                code = '',
            )

    def _node_comment(self):
        self._get_comment()
        if self.comment:
            self.node = PPML_Node_Comment(
                parent = self,
                code = self.code,
            )
            self.node.comments.append( self.comment )

    def _node_option(self):
        m=re.match('^(=\s*([^\s]+))', self.ccode)
        if not m:
            return None
        self.node = PPML_Node_Option(
            parent = self,
            code = self.code,
            value = m.group(2),
        )
        self._strip(m.group(1))
        
        self._get_units(node=True)
        self._get_comment(node=True)
    
    def _node_group(self):
        if self._isempty():
            self.node = PPML_Node_Group(
                parent = self,
                code = self.code,
                name = self.name,
            )

    def _node_mod(self):
        # Parse modification without type
        m=re.match('^(=\s+([^#\s]+))', self.ccode)
        if m:
            self.node = PPML_Node_Mod(
                parent = self,
                code = self.code,
                value = m.group(2),
                name = self.name,
            )
            self._strip(m.group(1))
            
            self._get_comment(node=True)
    
    def _node_type(self):
        types = [
            PPML_Node_Boolean,
            PPML_Node_Integer,
            PPML_Node_Float,
            PPML_Node_String,
            PPML_Node_Table,
        ]
        for nd in types:
           node_try = nd(
               parent = self,
               code = self.code,
               name = self.name,
           )
           if node_try.dtname==self.ccode[0:len(node_try.dtname)]:
               self.node = node_try
               break
        if self.node is None:
            raise Exception(f"Type not recognized: {self.code}")
        self._strip(self.node.dtname)

        # Parse if parameter has to be defined
        if self.ccode[:1]=='!':
            self.node.defined = True
            self._strip('!')

        # Parse array settings
        pattern = '^(\[([0-9:]+)\])'
        m=re.match(pattern, self.ccode)
        if m: self.node.dimension = []
        while m:
            if ":" not in m.group(2):
                self.node.dimension.append((int(m.group(2)),int(m.group(2))))
            else:
                dmin,dmax = m.group(2).split(':')
                self.node.dimension.append((
                    int(dmin) if dmin else None,
                    int(dmax) if dmax else None
                ))
            self._strip(m.group(1))
            m=re.match(pattern, self.ccode)

        # Parse equal sign
        m=re.match('^(=\s+)', self.ccode)
        if m:
            self._strip(m.group(1))
        else:
            raise Exception("Definition does not have a correct format")

        # Parse value
        m=re.match('^("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+))', self.ccode)
        if m:
            # Reduce matches
            results = [x for x in m.groups() if x is not None]
            # Save value
            if self.node.dimension:
                self.node.value = np.array(json.loads(results[1]), dtype=self.node.dtcast)
            else:
                self.node.value = self.node.dtcast(results[1])
            self._strip(m.group(1))
        if self.node.value is None:
            raise Exception("Value has to be set after equal sign")

        self._get_units(node=True)
        self._get_comment(node=True)
    
    def process_code(self):
        self.ccode = self.code
        steps = [
            self._node_empty,    # parse empty line node
            self._get_indent,  # parse line indent
            self._node_comment,  # parse comment node
            self._node_option,   # parse option node
            self._get_name,    # parse node name
            self._node_group,    # parse group node
            self._node_mod,      # parse base node (modification)
            self._node_type,     # parse type node
        ]
        for step in steps:
            step()
            if self.node and self._isempty():
                return self.node
        raise Exception(f"Incorrect format: {self.code}")

class PPML_Node(BaseModel):
    code: str 
    line: int
    source: str
    dtname: str
    indent: int = 0
    name: str = None

    value: int = None
    comments: str = []
    defined: bool = False
    dimension: List[tuple] = None
    units: str = None

    def __init__(self, **kwargs):
        if 'parent' in kwargs:
            parent = kwargs['parent']
            del kwargs['parent']
            kwargs['line'] = parent.line
            kwargs['source'] = parent.source
            kwargs['indent'] = parent.indent
        super().__init__(**kwargs)
            
class PPML_Node_Empty(PPML_Node):
    dtname: str = 'empty'
    code: str = ''
    value: str = None

class PPML_Node_Mod(PPML_Node):
    dtname: str = 'mod'
    value: str = None

class PPML_Node_Group(PPML_Node):
    dtname: str = 'group'
    code: str = ''
    value: str = None

class PPML_Node_Comment(PPML_Node):
    dtname: str = 'comment'
    dtcast = str
    value: str = None

class PPML_Node_Option(PPML_Node):
    dtname: str = 'option'
    value: str = None
    
class PPML_Node_Boolean(PPML_Node):
    value: bool = None
    dtname: str = 'bool'
    dtcast = bool
    
class PPML_Node_Integer(PPML_Node):
    value: int = None
    dtname: str = 'int'
    dtcast = int
    options = []

class PPML_Node_Float(PPML_Node):
    value: float = None
    dtname: str = 'float'
    dtcast = float
    options = []

class PPML_Node_String(PPML_Node):
    value: str = None
    dtname: str = 'str'
    dtcast = str
    options = []

class PPML_Node_Table(PPML_Node):
    value: str = None
    dtname: str = 'table'
    dtcast = str


