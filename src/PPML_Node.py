from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re
import json

class PPML_Node(BaseModel):
    code: str
    line: int
    source: str
    
    indent: int = 0
    name: str = None
    comments: str = None
    defined: bool = False
    dimension: List[tuple] = None
    units: str = None
    
    def match(self):        
        # Empty line
        if self.code.strip()=="":
            return False

        # Parse indent
        m=re.match('^(\s*)',self.code)
        if m:
            self.indent = len(m.group(1))
            self.code = self.code.lstrip()

        # Parse comment line
        m=re.match('^#\s*(.*)', self.code)
        if m:
            node = PPML_Node_Comment(
                code = self.code,
                line = self.line,
                source = self.source,
            )
            node.comments = node.dtcast(m.group(1))
            return node
            
        # Parse name
        m=re.match('^([a-zA-Z0-9_-]*)', self.code)
        if m:
            self.name = m.group(1)
            self.code = self.code[len(m.group(1)):].lstrip()
        else:
            raise Exception("Name has an invalid format: "+self.code)

        # Parse type
        if self.dtname==self.code[0:len(self.dtname)]:
            self.code = self.code[len(self.dtname):]
        else:
            return False    

        # Parse if parameter has to be defined
        if self.code[:1]=='!':
            self.defined = True
            self.code = self.code[1:]

        # Parse array settings
        pattern = '^\[([0-9:]+)\]'
        m=re.match(pattern, self.code)
        if m: self.dimension = []
        while m:
            if ":" not in m.group(1):
                self.dimension.append((int(m.group(1)),int(m.group(1))))
            else:
                dmin,dmax = m.group(1).split(':')
                self.dimension.append((
                    int(dmin) if dmin else None,
                    int(dmax) if dmax else None
                ))
            self.code = self.code[len(m.group(1))+2:]
            m=re.match(pattern, self.code)

        # Parse equal sign
        m=re.match('^(\s+=\s+)', self.code)
        if m:
            self.code = self.code[len(m.group(1)):]
        elif self.code.strip()=="":
            return self
        else:
            raise Exception("Definition does not have a correct format")
        
        # Parse value
        m=re.match('^("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+))', self.code)
        if m:
            # Reduce matches
            results = [x for x in m.groups() if x is not None]
            # Save value
            if self.dimension:
                self.value = np.array(json.loads(results[1]), dtype=self.dtcast)
            else:
                self.value = self.dtcast(results[1])
            self.code = self.code[len(m.group(1)):]
        if self.value is None:
            raise Exception("Value has to be set after equal sign")

        # Parse units
        m=re.match('^(\s*([^# ]+))', self.code)
        if m:
            self.units = m.group(2)
            self.code = self.code[len(m.group(1)):].lstrip()

        # Parse comments
        m=re.match('^(\s*#\s*(.*))', self.code)
        if m:
            self.comments = m.group(2)
            self.code = self.code[len(m.group(1)):].lstrip()

        # Is something left?
        if len(self.code.strip())>0:
            raise Exception("Definition format is incorrect")
        
        return self
            
class PPML_Node_Empty(PPML_Node):
    pass

class PPML_Node_Comment(PPML_Node):
    dtname: str = 'comment'
    dtcast = str

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

