from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re
import json

class PPML_Node(BaseModel):
    code: str
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

    def parse_empty(self):
        return PPML_Node_Empty(
            line = self.line,
            source = self.source,
            indent = self.indent,
        )

    def parse_comment(self, m):
        node = PPML_Node_Comment(
            code = self.code,
            line = self.line,
            source = self.source,
            indent = self.indent,
        )
        node.comments.append( node.dtcast(m.group(1)) )
        return node

    def parse_option(self, code):
        node = PPML_Node_Option(
            code = self.code,
            line = self.line,
            source = self.source,
            indent = self.indent,
            value = code,
        )
        return node
    
    def parse_group(self):
        return PPML_Node_Group(
            code = self.code,
            line = self.line,
            source = self.source,
            name = self.name,
            indent = self.indent,
        )

    def parse_type(self, code):
        node = None
        for nd in PPML_Nodes:
           node_try = nd(
               code = self.code,
               line = self.line,
               source = self.source,
               name = self.name,
               indent = self.indent,
           )
           if node_try.dtname==code[0:len(node_try.dtname)]:
               node = node_try
               break
        if node is None:
            return False

        code = code[len(node.dtname):]

        # Parse if parameter has to be defined
        if code[:1]=='!':
            node.defined = True
            code = code[1:]

        # Parse array settings
        pattern = '^\[([0-9:]+)\]'
        m=re.match(pattern, code)
        if m: node.dimension = []
        while m:
            if ":" not in m.group(1):
                node.dimension.append((int(m.group(1)),int(m.group(1))))
            else:
                dmin,dmax = m.group(1).split(':')
                node.dimension.append((
                    int(dmin) if dmin else None,
                    int(dmax) if dmax else None
                ))
            code = code[len(m.group(1))+2:]
            m=re.match(pattern, code)

        # Parse equal sign
        m=re.match('^(\s+=\s+)', code)
        if m:
            code = code[len(m.group(1)):]
        else:
            raise Exception("Definition does not have a correct format")

        # Parse value
        m=re.match('^("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+))', code)
        if m:
            # Reduce matches
            results = [x for x in m.groups() if x is not None]
            # Save value
            if node.dimension:
                node.value = np.array(json.loads(results[1]), dtype=node.dtcast)
            else:
                node.value = node.dtcast(results[1])
            code = code[len(m.group(1)):]
        if node.value is None:
            raise Exception("Value has to be set after equal sign")

        # Parse units
        m=re.match('^(\s*([^# ]+))', code)
        if m:
            node.units = m.group(2)
            code = code[len(m.group(1)):].lstrip()

        # Parse comments
        m=re.match('^(\s*#\s*(.*))', code)
        if m:
            node.comments.append( m.group(2) )
            code = code[len(m.group(1)):].lstrip()

        # Is something left?
        if len(code.strip())>0:
            raise Exception("Definition format is incorrect")

        return node      
    
    def process_code(self):
        code = self.code
        
        # Empty line
        if code.strip()=="":
            return self.parse_empty()

        # Parse indent
        m=re.match('^(\s*)',code)
        if m:
            self.indent = len(m.group(1))
            code = code.lstrip()

        # Parse comment line
        m=re.match('^#\s*(.*)', code)
        if m:
            return self.parse_comment(m)

        # Parse option line
        m=re.match('^=\s*(.+)', code)
        if m:
            return self.parse_option(m.group(1))
        
        # Parse name
        m=re.match('^([a-zA-Z0-9_-]*)', code)
        if m:
            self.name = m.group(1)
            code = code[len(m.group(1)):].lstrip()
        else:
            raise Exception("Name has an invalid format: "+code)
        # Parse group node
        if code.strip()=="":
            return self.parse_group()
        
        # Parse type
        return self.parse_type(code)
            
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

class PPML_Node_Float(PPML_Node):
    value: float = None
    dtname: str = 'float'
    dtcast = float

class PPML_Node_String(PPML_Node):
    value: str = None
    dtname: str = 'str'
    dtcast = str

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

