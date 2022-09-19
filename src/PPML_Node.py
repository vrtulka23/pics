from typing import List
from pydantic import BaseModel

from PPML_Datatype import *

class PPML_Node(BaseModel):

    code: str
    nodes: List = []
    file: str = None
    line: int = None

    name: str = None
    value: PPML_Datatype = None
    
    def parse_code(self):
        for dt in PPML_Datatypes:
            datatype = dt().match(self.code)
            if datatype:
                self.value = datatype
                print(datatype)
