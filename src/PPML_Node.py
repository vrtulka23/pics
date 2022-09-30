from typing import List,Tuple
from pydantic import BaseModel
import numpy as np
import re
import json

class PPML_Node(BaseModel):
    indent: int = 0;
    name: str = None;
    comments: str = None;
    defined: bool = False;
    dimension: List[tuple] = None
    units: str = None;
    
    def match(self, code: str):
        # Empty line
        if code.strip()=="":
            return False

        # Parse indent
        m=re.match('^(\s*)',code)
        if m:
            self.indent = len(m.group(1))
            code = code.lstrip()
            
        # Parse name
        m=re.match('^([a-zA-Z0-9_-]+)', code)
        if m:
            self.name = m.group(1)
            code = code[len(m.group(1)):].lstrip()
        else:
            raise Exception("Name has an invalid format: "+code)

        # Parse type
        if self.dtname==code[0:len(self.dtname)]:
            code = code[len(self.dtname):]
        else:
            return False    

        # Parse if parameter has to be defined
        if code[:1]=='!':
            self.defined = True
            code = code[1:]

        # Parse array settings
        pattern = '^\[([0-9:]+)\]'
        m=re.match(pattern, code)
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
            code = code[len(m.group(1))+2:]
            m=re.match(pattern, code)

        # Parse equal sign
        m=re.match('^(\s+=\s+)', code)
        if m:
            code = code[len(m.group(1)):]
        elif code.strip()=="":
            return self
        else:
            raise Exception("Definition does not have a correct format")

        # Add replacement marks
        replace = ["\\'", '\\"', "\n"]
        for i,symbol in enumerate(replace):
            code = code.replace(symbol,f"$#@{i:02d}")
        
        # Parse value
        m=re.match('^("""(.*)"""|"(.*)"|\'(.*)\'|([^# ]+))', code)
        if m:
            # Reduce matches
            results = [x for x in m.groups() if x is not None]
            # Remove replacement marks
            replace = ["\'", '\"', "\n"]
            for i,symbol in enumerate(replace):
                  results[1] = results[1].replace(f"$#@{i:02d}", symbol)
            # Save value
            if self.dimension:
                self.value = np.array(json.loads(results[1]), dtype=self.dtcast)
            else:
                self.value = self.dtcast(results[1])
            code = code[len(m.group(1)):]
        if self.value is None:
            raise Exception("Value has to be set after equal sign")

        # Parse units
        m=re.match('^(\s*([^# ]+))', code)
        if m:
            self.units = m.group(2)
            code = code[len(m.group(1)):].lstrip()

        # Parse comments
        m=re.match('^(\s*#\s*(.*))', code)
        if m:
            self.comments = m.group(2)
            code = code[len(m.group(1)):].lstrip()

        # Is something left?
        if len(code.strip())>0:
            raise Exception("Definition format is incorrect")
        
        return self
            
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

