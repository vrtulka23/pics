from typing import List
from pydantic import BaseModel

class PPML_Type(BaseModel):
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
    options: List[str] = None
    
    def __init__(self, parent):
        kwargs = {}
        kwargs['line'] = parent.line
        kwargs['source'] = parent.source
        kwargs['indent'] = parent.indent
        kwargs['code'] = parent.code
        kwargs['name'] = parent.name
        super().__init__(**kwargs)
            
class PPML_Type_Empty(PPML_Type):
    dtname: str = 'empty'
    code: str = ''
    value: str = None

class PPML_Type_Mod(PPML_Type):
    dtname: str = 'mod'
    value: str = None
    dtcast = str

class PPML_Type_Group(PPML_Type):
    dtname: str = 'group'
    code: str = ''
    value: str = None

class PPML_Type_Comment(PPML_Type):
    dtname: str = 'comment'
    value: str = None
    dtcast = str

class PPML_Type_Option(PPML_Type):
    dtname: str = 'option'
    value: str = None
    dtcast = str
    
class PPML_Type_Boolean(PPML_Type):
    value: bool = None
    dtname: str = 'bool'
    dtcast = bool
    
class PPML_Type_Integer(PPML_Type):
    value: int = None
    dtname: str = 'int'
    dtcast = int
    options: List[int] = []

class PPML_Type_Float(PPML_Type):
    value: float = None
    dtname: str = 'float'
    dtcast = float
    options: List[float] = []

class PPML_Type_String(PPML_Type):
    value: str = None
    dtname: str = 'str'
    dtcast = str
    options: List[str] = []

class PPML_Type_Table(PPML_Type):
    value: str = None
    dtname: str = 'table'
    dtcast = str


