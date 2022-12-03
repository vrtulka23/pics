import numpy as np
import re
from math import isclose

from PPML_Unit import *
from PPML_UnitList import *
        
class PPML_Converter:

    base: dict = {}
    prefixes: dict = {}
    derivates: dict = {}
    units: dict = {}
    
    def __init__(self):
        self.nbase = len(PPML_UnitList_Base)
        self.npbase = self.nbase-3
        # Load unit lists into dictionaries
        for unit in PPML_UnitList_Base:
            self.base[unit[2]] = PPML_Unit(
                unit[0], unit[1], symbol=unit[2], dfn=unit[3], name=unit[4]
            )
        for unit in PPML_UnitList_Prefixes:
            self.prefixes[unit[2]] = PPML_Unit(
                unit[0], unit[1], symbol=unit[2], dfn=unit[3], name=unit[4]
            )
        for unit in PPML_UnitList_Derivates:
            self.derivates[unit[2]] = PPML_Unit(
                unit[0], unit[1], symbol=unit[2], dfn=unit[3], name=unit[4]
            )
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
        # parse unit
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
