from typing import List
from pydantic import BaseModel
import numpy as np
import json

class PPML_Type(BaseModel):
    code: str 
    line: int
    source: str
    keyword: str
    
    dtype = str
    indent: int = 0
    name: str = None
    value: str = None
    defined: bool = False
    units: str = None
    comments: str = []
    dimension: List[tuple] = None
    options: List[BaseModel] = None
    mods: List[BaseModel] = []
    
    def __init__(self, parent):
        kwargs = {}
        kwargs['line'] = parent.line
        kwargs['source'] = parent.source
        kwargs['indent'] = parent.indent
        kwargs['code'] = parent.code
        kwargs['name'] = parent.name
        super().__init__(**kwargs)
            
class PPML_Type_Empty(PPML_Type):
    keyword: str = 'empty'

class PPML_Type_Mod(PPML_Type):
    keyword: str = 'mod'

class PPML_Type_Group(PPML_Type):
    keyword: str = 'group'

class PPML_Type_Comment(PPML_Type):
    keyword: str = 'comment'

class PPML_Type_Option(PPML_Type):
    keyword: str = 'option'
    
class PPML_Type_Boolean(PPML_Type):
    keyword: str = 'bool'
    value: bool = None
    dtype = bool
    
class PPML_Type_Integer(PPML_Type):
    keyword: str = 'int'
    value: int = None
    options: List[BaseModel] = []
    dtype = int

class PPML_Type_Float(PPML_Type):
    keyword: str = 'float'
    value: float = None
    options: List[BaseModel] = []
    dtype = float

class PPML_Type_String(PPML_Type):
    keyword: str = 'str'

class PPML_Type_Table(PPML_Type):
    keyword: str = 'table'


