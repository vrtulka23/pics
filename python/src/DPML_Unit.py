from pydantic import BaseModel
from typing import List

class DPML_Unit(BaseModel):
    num: float         # number value
    base: List[int]    # unit dimension exponents
    dfn: str = None    # definition expression
    symbol: str = None # symbol
    symbol_base: str = None  # symbol without prefix
    name: str = None   # full name
    arbitrary: bool = False  # is unit arbitrary?

    def __init__(self,num,base=None,**kwargs):
        kwargs['num'] = num
        kwargs['base'] = base
        super().__init__(**kwargs)

