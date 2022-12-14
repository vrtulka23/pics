import numpy as np
import re
from math import isclose

from DPML_Unit import *
from DPML_UnitList import *
from DPML_Settings import *

class DPML_Converter:

    base: dict = {}
    prefixes: dict = {}
    derivates: dict = {}
    arbitrary: dict = {}
    custom: dict = {}
    units: dict = {}
    
    def __init__(self, units=None):
        self.nbase = len(DPML_UnitList_Base)
        self.npbase = self.nbase-1
        # Load unit lists into dictionaries
        for unit in DPML_UnitList_Base:
            self.base[unit[2]] = DPML_Unit(
                unit[0], unit[1], symbol=unit[2], name=unit[3]
            )
        for unit in DPML_UnitList_Prefixes:
            self.prefixes[unit[2]] = DPML_Unit(
                unit[0], unit[1], symbol=unit[2], dfn=unit[3], name=unit[4]
            )
        for unit in DPML_UnitList_Derivates:
            self.derivates[unit[2]] = DPML_Unit(
                unit[0], unit[1], symbol=unit[2], dfn=unit[3], name=unit[4]
            )
        for unit in DPML_UnitList_Arbitrary:
            self.arbitrary[unit[1]] = DPML_Unit(
                1.0, unit[0], symbol=unit[1], name=unit[2], arbitrary=True
            )
        self.units = self.base | self.derivates | self.arbitrary
        if units:
            for unit in units:
                print(unit.symbol)
                if unit.symbol in self.units:
                    raise Exception('Following unit already exits:', unit.symbol)
                self.custom[unit.symbol] = unit
            self.units = self.units | self.custom

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        pass
    
    def equal(self, unit1, unit2):
        if not isclose(unit1.num, unit2.num, rel_tol=EQUAL_PRECISION):
            return False
        if unit1.base!=unit2.base:
            return False
        return True

    def _rebase(self, unit):
        exp = int(np.floor(np.log10(unit.num)))
        num = unit.num/10**exp
        unit.num = num
        unit.base[-1] += exp
        return unit
    
    def multiply(self, unit1, unit2):
        num = unit1.num*unit2.num
        base = [unit1.base[i]+unit2.base[i] for i in range(self.nbase)]
        return self._rebase(DPML_Unit(num, base))

    def divide(self, unit1, unit2):
        num = unit1.num/unit2.num
        base = [unit1.base[i]-unit2.base[i] for i in range(self.nbase)]
        return self._rebase(DPML_Unit(num, base))

    def power(self, unit, power):
        num = unit.num**power
        base = [unit.base[i]*power for i in range(self.nbase)]
        return self._rebase(DPML_Unit(num, base))

    def unit(self, string=None):
        # parse number
        m = re.match('^([0-9.]+)(e([0-9+-]+)|)$', string)
        if m:
            num = float(string)
            base = [0]*self.nbase
            return self._rebase(DPML_Unit(num, base))
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
        unit.arbitrary = self.units[base].arbitrary
        unit.symbol_base = base
        #print("%-06s"%string_bak, "%-03s"%prefix, "%-03s"%base, "%03s"%exp, unit)
        return unit

    def expression(self, right, expr_bak=None):
        if not expr_bak:
            expr_bak = right
        if right.count('(')!=right.count(')'):
            raise Exception(f"Unmatched parentheses in: {expr_bak}")
        left = ''
        symbol, right = right[0], right[1:]
        parentheses = 0
        while right:
            if symbol=='*':
                return self.multiply(
                    self.expression(left, expr_bak),
                    self.expression(right, expr_bak)
                )
            elif symbol=='/':
                if '/' in right:
                    # If there are multiple divisions
                    # we need to start from the last
                    parts = right.split('/')
                    right = parts.pop()
                    parts.insert(0,left)
                    left = '/'.join(parts)
                return self.divide(
                    self.expression(left, expr_bak),
                    self.expression(right, expr_bak)
                )
            elif symbol=='(':
                parentheses = 1
                symbol, right = right[0], right[1:]
                while parentheses>0:
                    if symbol=='(':
                        parentheses+=1
                    elif symbol==')':
                        parentheses-=1
                    else:
                        left = left + symbol
                    if not right:
                        return self.expression(left)
                    symbol, right = right[0], right[1:]
            else:
                left = left + symbol
                symbol, right = right[0], right[1:]
        unit = self.unit(left+symbol)
        unit.symbol = expr_bak
        return unit
        
    def convert(self, value, exp1, exp2):
        unit1 = self.expression(exp1)
        unit2 = self.expression(exp2)
        factor = self.divide(unit1,unit2)
        if factor.base[:self.npbase]!=[0]*self.npbase:
            raise Exception(f"Units '{exp1}' and '{exp2}' cannot be converted")
        if unit1.arbitrary or unit2.arbitrary:
            return DPML_Convert_Arbitrary(value, unit1, unit2)
        else:
            value *= factor.num
            value *= 10**factor.base[self.base['1e'].base.index(1)]
            return value
