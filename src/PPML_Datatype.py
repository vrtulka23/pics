from typing import List,Tuple
from pydantic import BaseModel
import re

class PPML_Datatype(BaseModel):
    indent: int = 0;
    name: str = None;
    comment: str = None;
    constrains: Tuple[int,int] = None;
    defined: bool = False;
    
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
        m=re.match('([a-zA-Z0-9_-]+)',code)
        if m:
            self.name = m.group(1)
            code = code[len(m.group(1)):].lstrip()
        else:
            raise Exception("Name has an invalid format: "+code)

        # Parse type
        if self.datatype==code[0:len(self.datatype)]:
            code = code[len(self.datatype):]
        else:
            return False    

        # Parse if parameter has to be defined
        if code[:1]=='!':
            self.defined = True
            code = code[1:]

        # Parse array settings
        """
        m=re.match('(\[([0-9:]+):([0-9:]+)\]|\[([0-9:]+)\]|!)',code)
        if m:
            if m.group(1)=="!":
                self.defined = True
            elif len(m.groups())==2:
                self
            print(m.group(1))
        """
        
        del self.patterns
        """
        re_indent = '^(\s*)'
        re_name = '([^=# ]+)'
        re_comment = '\s*(#\s*(.*)|)$'
        for p,pattern in enumerate(self.patterns):
            pattern = re_indent + re_name + pattern + re_comment
            match = re.match(pattern,repr(code)[1:-1])
            if match:
                print(code)
                self.indent = len(match.group(1))
                self.case = p
                self.name = match.group(2)
                self.parse(match)
                comment = match.group(len(match.groups()))
                self.comment = comment if comment else None
                del self.patterns
                return self
        """
        return self
            
class PPML_Datatype_Boolean(PPML_Datatype):
    value: bool = None
    datatype: str = 'bool'
    patterns: List[str] = [
        "\s+bool\s+=\s+([^# ]+)",
    ]
    def parse(self, match):
        self.value = bool(match.group(3))

class PPML_Datatype_Integer(PPML_Datatype):
    value: int = None
    datatype: str = 'int'
    patterns: List[str] = [
        "\s+int\s+=\s+([^# ]+)",
    ]
    def parse(self, match):
        self.value = int(match.group(3))

class PPML_Datatype_Float(PPML_Datatype):
    value: float = None
    datatype: str = 'float'
    patterns: List[str] = [
        "\s+float\s+=\s+([^# ]+)",
    ]
    def parse(self, match):
        self.value = float(match.group(3))

class PPML_Datatype_String(PPML_Datatype):
    value: str = None
    datatype: str = 'str'
    patterns: List[str] = [
        '\s+str\s+=\s+"""(.*)"""',        
        '\s+str\s+=\s+"(.*)"',        
        "\s+str\s+=\s+'(.*)'",        
        "\s+str\s+=\s+([^#]+)",        
    ]
    def parse(self, match):
        self.value = str(match.group(3))

class PPML_Datatype_Table(PPML_Datatype):
    datatype: str = 'table'
    patterns: List[str] = [
    ]

PPML_Datatypes = [
    PPML_Datatype_Boolean,
    PPML_Datatype_Integer,
    PPML_Datatype_Float,
    PPML_Datatype_String,
    PPML_Datatype_Table,
]

