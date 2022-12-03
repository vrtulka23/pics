from pydantic import BaseModel
from typing import List
import numpy as np
import re
from math import isclose

class PPML_Unit(BaseModel):
    num: float
    base: List[int]
    definition: str = None
    name: str = None

    def __init__(self,num,base,definition=None,name=None,**kwargs):
        kwargs['num'] = num
        kwargs['base'] = base
        kwargs['definition'] = definition
        kwargs['name'] = name
        super().__init__(**kwargs)

class PPML_Converter:

    base = {
        # physical units
        'm':    PPML_Unit(1.0, [1,0,0,0,0,0,0,0,0]),  # 1
        'g':    PPML_Unit(1.0, [0,1,0,0,0,0,0,0,0]),  # 2
        's':    PPML_Unit(1.0, [0,0,1,0,0,0,0,0,0]),  # 3
        'K':    PPML_Unit(1.0, [0,0,0,1,0,0,0,0,0]),  # 4
        'C':    PPML_Unit(1.0, [0,0,0,0,1,0,0,0,0]),  # 5
        'cd':   PPML_Unit(1.0, [0,0,0,0,0,1,0,0,0]),  # 6
        # numerical units
        'mol':  PPML_Unit(1.0, [0,0,0,0,0,0,1,0,0]),  # 7
        'rad':  PPML_Unit(1.0, [0,0,0,0,0,0,0,1,0]),  # 8
        '1e':   PPML_Unit(1.0, [0,0,0,0,0,0,0,0,1]),  # 9
    }
    derivates = { # m,g,s,K,C,cd,mol,rad,10
        # SI units
        'sr':    PPML_Unit(1.0,  [ 0, 0, 0, 0, 0, 0, 0, 2, 0], 'rad2',    'steradian'),
        'Hz':    PPML_Unit(1.0,  [ 0, 0,-1, 0, 0, 0, 0, 0, 0], 's-1',     'hertz'    ),
        'N':     PPML_Unit(1.0,  [ 1, 1,-2, 0, 0, 0, 0, 0, 3], 'kg*m/s2', 'newton'   ),
        'Pa':    PPML_Unit(1.0,  [-1, 1,-2, 0, 0, 0, 0, 0, 3], 'N/m2',    'pascal'   ),
        'J':     PPML_Unit(1.0,  [ 2, 1,-2, 0, 0, 0, 0, 0, 3], 'N*m',     'joule'    ),
        'W':     PPML_Unit(1.0,  [ 2, 1,-3, 0, 0, 0, 0, 0, 3], 'J/s',     'watt'     ),
        'A':     PPML_Unit(1.0,  [ 0, 0,-1, 0, 1, 0, 0, 0, 0], 'C/s',     'ampere'   ),
        'V':     PPML_Unit(1.0,  [ 2, 1,-2, 0,-1, 0, 0, 0, 3], 'J/C',     'volt'     ),
        'F':     PPML_Unit(1.0,  [-2,-1, 2, 0, 2, 0, 0, 0,-3], 'C/V',     'farad'    ),
        'Ohm':   PPML_Unit(1.0,  [ 2, 1,-1, 0,-2, 0, 0, 0, 3], 'V/A',     'ohm'      ),
        'S':     PPML_Unit(1.0,  [-2,-1, 1, 0, 2, 0, 0, 0,-3], 'Ohm-1',   'siemens'  ),
        'Wb':    PPML_Unit(1.0,  [ 2, 1,-1, 0,-1, 0, 0, 0, 3], 'V*s',     'weber'    ),
        'T':     PPML_Unit(1.0,  [ 0, 1,-1, 0,-1, 0, 0, 0, 3], 'Wb/m2',   'tesla'    ),
        'H':     PPML_Unit(1.0,  [ 2, 1, 0, 0,-2, 0, 0, 0, 3], 'Wb/A',    'henry'    ),
        'lm':    PPML_Unit(1.0,  [ 0, 0, 0, 0, 0, 1, 0, 2, 0], 'cd*sr',   'lumen'    ),
        'lx':    PPML_Unit(1.0,  [-2, 0, 0, 0, 0, 1, 0, 2, 0], 'lm/m2',   'lux'      ),
        'Bq':    PPML_Unit(1.0,  [ 0, 0,-1, 0, 0, 0, 0, 0, 0], 's-1',     'becquerel'),
        'Gy':    PPML_Unit(1.0,  [ 2, 0,-2, 0, 0, 0, 0, 0, 0], 'J/kg',    'gray'     ),
        'Sv':    PPML_Unit(1.0,  [ 2, 0,-2, 0, 0, 0, 0, 0, 0], 'J/kg',    'sivert'   ),
        # CGS units                          
        'dyn':   PPML_Unit(1.0,  [ 1, 1,-2, 0, 0, 0, 0, 0,-2], 'g*cm/s2', 'dyne'     ),
        'erg':   PPML_Unit(1.0,  [ 2, 1,-2, 0, 0, 0, 0, 0,-4], 'dyn*cm',  'erg'      ),
        'G':     PPML_Unit(1.0,  [ 0, 1,-1, 0,-1, 0, 0, 0,-1], '1e-4*T',  'Gauss'    ),
        # other derived units
        'deg':   PPML_Unit(1.745329,   [ 0, 0, 0, 0, 0,0,0,1, -2],
                           '2*[pi]*rad/360', 'degree'       ),
        'eV':    PPML_Unit(1.60217733, [ 2, 1,-2, 0, 0,0,0,0,-16],
                           '[e]*V',        'electronvolt'),
        # natural units                                           
        '[e]':   PPML_Unit(1.60217733,        [ 0, 0, 0, 0, 1, 0, 0, 0,-19],
                           None, 'elementary charge'),
        # dimensionless units
        '[pi]':    PPML_Unit(np.pi,      [0,0,0,0,0,0,0,0, 0], '3.141593', 'pi'),
        '[euler]': PPML_Unit(np.e,       [0,0,0,0,0,0,0,0, 0], '2.718282', "Euler's num."),
        '[N_A]':   PPML_Unit(6.0221367,  [0,0,0,0,0,0,0,0,23], '6.022137e23', "Avogadro's num."),
    }
    prefixes = {  
        'Y':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, 24]),  # yotta
        'Z':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, 21]),  # zetta
        'E':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, 18]),  # exa
        'P':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, 15]),  # peta
        'T':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, 12]),  # tera
        'G':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,  9]),  # giga
        'M':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,  6]),  # mega
        'k':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,  3]),  # kilo
        'h':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,  2]),  # hectoh
        'da':   PPML_Unit(1.0, [0,0,0,0,0,0,0,0,  1]),  # deka
        'd':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, -1]),  # deci
        'c':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, -2]),  # centi
        'm':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, -3]),  # milli
        'u':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, -6]),  # micro
        'n':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0, -9]),  # nano
        'p':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,-12]),  # pico
        'f':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,-15]),  # femto
        'a':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,-18]),  # atto
        'z':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,-21]),  # zepto
        'y':    PPML_Unit(1.0, [0,0,0,0,0,0,0,0,-24]),  # yocto
    }
    other = {
        'Cel':   PPML_Unit(1.0,  [0, 0, 0, 1, 0, 0, 0, 0, 0]), 	# degree (cel(1 K))
    }

    def __init__(self):
        self.nbase = len(self.base)
        self.npbase = self.nbase-3
        self.units = self.base | self.derivates

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        pass
    
    def equal(self, unit1, unit2):
        if not isclose(unit1.num, unit2.num, rel_tol=1e-6):
            return False
        if unit1.base!=unit2.base:
            return False
        return True
    
    def multiply(self, unit1, unit2):
        num = unit1.num*unit2.num
        base = [unit1.base[i]+unit2.base[i] for i in range(self.nbase)]
        return PPML_Unit(num, base)

    def divide(self, unit1, unit2):
        num = unit1.num/unit2.num
        base = [unit1.base[i]-unit2.base[i] for i in range(self.nbase)]
        return PPML_Unit(num, base)

    def power(self, unit, power):
        num = unit.num**power
        base = [unit.base[i]*power for i in range(self.nbase)]
        return PPML_Unit(num, base)

    def unit(self, string):
        # parse number
        m = re.match('^([0-9.]+)(e([0-9+-]+)|)$', string)
        if m:
            number = float(string)
            exp = int(np.floor(np.log10(number)))
            unit = self.base['1e'].copy()
            unit.num = number/10**exp
            unit.base = [b*exp for b in unit.base]
            return unit
        # parse 
        string_bak = string
        exp, base, prefix = '', '', ''
        symbol, string = string[-1], ' '+string[:-1]
        # parse exponent
        while len(string):
            if not re.match('^[0-9+-]{1}$', symbol):
                break
            exp = symbol+exp
            symbol, string = string[-1], string[:-1]
        # parse unit symbol
        unitkeys = self.units.keys()
        while len(string):
            nbase = len(base)+1
            ukeys = [key[-nbase:] for key in unitkeys]
            if symbol+base not in ukeys:
                break
            base = symbol+base
            symbol, string = string[-1], string[:-1]
        # parse unit prefix
        while len(string):
            prefix = symbol+prefix
            symbol, string = string[-1], string[:-1]
            if symbol==' ':
                break
        # apply prefix
        if prefix:
            if prefix not in self.prefixes.keys():
                raise Exception(f"Unit prefix '{prefix}' is not available in: {string_bak}")
            unit = self.multiply(self.prefixes[prefix],self.units[base])
        else:
            unit = self.units[base]
        # apply exponent
        if exp:
            unit = self.power(unit,int(exp))
        #print("%-06s"%string_bak, "%-03s"%prefix, "%-03s"%base, "%03s"%exp, unit)
        return unit

    def expression(self, part2, expr_bak=None):
        if not expr_bak:
            expr_bak = part2
        if part2.count('(')!=part2.count(')'):
            raise Exception(f"Unmatched parentheses in: {expr_bak}")
        part1 = ''
        symbol, part2 = part2[0], part2[1:]
        parentheses = 0
        while part2:
            if symbol=='*':
                return self.multiply(
                    self.expression(part1, expr_bak),
                    self.expression(part2, expr_bak)
                )
            elif symbol=='/':
                if '/' in part2:
                    # If there are multiple divisions
                    # we need to start from the last
                    parts = part2.split('/')
                    part2 = parts.pop()
                    parts.insert(0,part1)
                    part1 = '/'.join(parts)
                return self.divide(
                    self.expression(part1, expr_bak),
                    self.expression(part2, expr_bak)
                )
            elif symbol=='(':
                parentheses = 1
                symbol, part2 = part2[0], part2[1:]
                while parentheses>0:
                    if symbol=='(':
                        parentheses+=1
                    elif symbol==')':
                        parentheses-=1
                    else:
                        part1 = part1 + symbol
                    if not part2:
                        return self.expression(part1)
                    symbol, part2 = part2[0], part2[1:]
            else:
                part1 = part1 + symbol
                symbol, part2 = part2[0], part2[1:]
        return self.unit(part1+symbol)
        
    def convert(self, value, exp1, exp2):
        unit1 = self.expression(exp1)
        unit2 = self.expression(exp2)
        factor = self.divide(unit1,unit2)
        if factor.base[:self.npbase]!=[0]*self.npbase:
            raise Exception(f"Units '{exp1}' and '{exp2}' cannot be converted")
        value *=  factor.num
        value *= 10**factor.base[self.base['1e'].base.index(1)]
        return value
