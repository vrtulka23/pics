from pydantic import BaseModel
from typing import List

class PPML_Unit(BaseModel):
    num: float         # number value
    base: List[int]    # unit dimension exponents
    dfn: str = None    # definition expression
    symbol: str = None # symbol
    name: str = None   # full name

    def __init__(self,num,base,**kwargs):
        kwargs['num'] = num
        kwargs['base'] = base
        super().__init__(**kwargs)

