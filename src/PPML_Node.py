from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re
import json

class PPML_Node(BaseModel):
    code: str  # original code
    ccode: str # processed code
    line: int
    source: str

    value: int = None
    indent: int = 0
    name: str = None
    dtname: str = 'base'
    comments: str = []
    defined: bool = False
    dimension: List[tuple] = None
    units: str = None

    def __init__(self, **kwargs):
        kwargs['ccode'] = kwargs['code']
        super().__init__(**kwargs)
    
    def _ccode_strip(self, text):
        self.ccode = self.ccode[len(text):].lstrip()
        
    def _parse_empty(self):
        if not self.ccode.strip()=="":
            return None
        return PPML_Node_Empty(
            code = '',
            line = self.line,
            source = self.source,
            indent = self.indent,
        )

    def _parse_indent(self):
        m=re.match('^(\s*)',self.ccode)
        if m:
            self.indent = len(m.group(1))
            self._ccode_strip(m.group(1))
    
    def _parse_comment(self):
        m=re.match('^(#\s*(.*))', self.ccode)
        if not m:
            return None
        node = PPML_Node_Comment(
            code = self.code,
            line = self.line,
            source = self.source,
            indent = self.indent,
        )
        node.comments.append( node.dtcast(m.group(2)) )
        self._ccode_strip(m.group(1))
        return node

    def _parse_option(self):
        m=re.match('^(=\s*([^\s]+)(\s+[^\s#]+|)(\s+#(.+)|)\s*)', self.ccode)
        if not m:
            return None
        node = PPML_Node_Option(
            code = self.code,
            line = self.line,
            source = self.source,
            indent = self.indent,
            value = m.group(2).strip(),
        )
        if m.group(3):
            node.units = m.group(3).strip()
        if m.group(4):
            node.comments.append(m.group(4).strip())        
        self._ccode_strip(m.group(1))
        return node

    def _parse_name(self):
        m=re.match('^([a-zA-Z0-9_-]*)', self.ccode)
        if m:
            self.name = m.group(1)
            self._ccode_strip(m.group(1))
        else:
            raise Exception("Name has an invalid format: "+self.ccode)
    
    def _parse_group(self):
        if self.ccode.strip()!="":
            return None
        return PPML_Node_Group(
            code = self.code,
            line = self.line,
            source = self.source,
            name = self.name,
            indent = self.indent,
        )

    def _parse_base(self):
        # Parse modification without type
        m=re.match('^(\s*=\s+([^#\s]+)(\s*#\s*(.+)|))', self.ccode)
        if m:
            self.value = m.group(2)
            if m.group(3):
                self.comments.append(m.group(4))
            self._ccode_strip(m.group(1))
            return self
    
    def _parse_type(self):
        node = None
        for nd in PPML_Nodes:
           node_try = nd(
               code = self.code,
               line = self.line,
               source = self.source,
               name = self.name,
               indent = self.indent,
           )
           if node_try.dtname==self.ccode[0:len(node_try.dtname)]:
               node = node_try
               break
        if node is None:
            return node

        self._ccode_strip(node.dtname)

        # Parse if parameter has to be defined
        if self.ccode[:1]=='!':
            node.defined = True
            self._ccode_strip('!')

        # Parse array settings
        pattern = '^(\[([0-9:]+)\])'
        m=re.match(pattern, self.ccode)
        if m: node.dimension = []
        while m:
            if ":" not in m.group(2):
                node.dimension.append((int(m.group(2)),int(m.group(2))))
            else:
                dmin,dmax = m.group(2).split(':')
                node.dimension.append((
                    int(dmin) if dmin else None,
                    int(dmax) if dmax else None
                ))
            self._ccode_strip(m.group(1))
            m=re.match(pattern, self.ccode)

        # Parse equal sign
        m=re.match('^(\s*=\s+)', self.ccode)
        if m:
            self._ccode_strip(m.group(1))
        else:
            raise Exception("Definition does not have a correct format")

        # Parse value
        m=re.match('^("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+))', self.ccode)
        if m:
            # Reduce matches
            results = [x for x in m.groups() if x is not None]
            # Save value
            if node.dimension:
                node.value = np.array(json.loads(results[1]), dtype=node.dtcast)
            else:
                node.value = node.dtcast(results[1])
            self._ccode_strip(m.group(1))
        if node.value is None:
            raise Exception("Value has to be set after equal sign")

        # Parse units
        m=re.match('^(\s*([^# ]+))', self.ccode)
        if m:
            node.units = m.group(2)
            self._ccode_strip(m.group(1))

        # Parse comments
        m=re.match('^(\s*#\s*(.*))', self.ccode)
        if m:
            node.comments.append( m.group(2) )
            self._ccode_strip(m.group(1))

        return node      
    
    def process_code(self):
        self.ccode = self.code

        steps = [
            self._parse_empty,    # parse empty line node
            self._parse_indent,   # parse line indent
            self._parse_comment,  # parse comment node
            self._parse_option,   # parse option node
            self._parse_name,     # parse node name
            self._parse_group,    # parse group node
            self._parse_base,     # parse base node (modification)
            self._parse_type,     # parse type node
        ]
        for step in steps:
            node = step()
            if node:
                if len(self.ccode.strip())>0:
                    raise Exception(f"Incorrect format: {self.code}")
                return node
                    
class PPML_Node_Empty(PPML_Node):
    dtname: str = 'empty'
    code: str = ''
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

PPML_Nodes = [
    PPML_Node_Boolean,
    PPML_Node_Integer,
    PPML_Node_Float,
    PPML_Node_String,
    PPML_Node_Table,
]

