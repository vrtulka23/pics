from pydantic import BaseModel
import numpy as np
import re

class PUML_Parse:

    base = {
        # physical units
        'm':    (1.0, [1,0,0,0,0,0,0,0,0]),  # 1
        'g':    (1.0, [0,1,0,0,0,0,0,0,0]),  # 2
        's':    (1.0, [0,0,1,0,0,0,0,0,0]),  # 3
        'K':    (1.0, [0,0,0,1,0,0,0,0,0]),  # 4
        'C':    (1.0, [0,0,0,0,1,0,0,0,0]),  # 5
        'cd':   (1.0, [0,0,0,0,0,1,0,0,0]),  # 6
        # numerical units
        'mol':  (1.0, [0,0,0,0,0,0,1,0,0]),  # 7
        'rad':  (1.0, [0,0,0,0,0,0,0,1,0]),  # 8
        '10*':  (1.0, [0,0,0,0,0,0,0,0,1]),  # 9
    }
    derivates = { # m,g,s,K,C,cd,rad,10
        # SI units
        'sr':    (1.0,  [ 0, 0, 0, 0, 0, 0, 0, 2, 0]), 	# steradian (rad2)
        'Hz':    (1.0,  [ 0, 0,-1, 0, 0, 0, 0, 0, 0]), 	# hertz (s-1)
        'N':     (1.0,  [ 1, 1,-2, 0, 0, 0, 0, 0, 3]), 	# newton (kg.m/s2)
        'Pa':    (1.0,  [-1, 1,-2, 0, 0, 0, 0, 0, 3]), 	# pascal (N/m2)
        'J':     (1.0,  [ 2, 1,-2, 0, 0, 0, 0, 0, 3]), 	# joule (N.m)
        'W':     (1.0,  [ 2, 1,-3, 0, 0, 0, 0, 0, 3]), 	# watt (J/s)
        'A':     (1.0,  [ 0, 0,-1, 0, 1, 0, 0, 0, 0]), 	# ampere (C/s)
        'V':     (1.0,  [ 2, 1,-2, 0,-1, 0, 0, 0, 3]), 	# volt (J/C)
        'F':     (1.0,  [-2,-1, 2, 0, 2, 0, 0, 0,-3]), 	# farad (C/V)
        'Ohm':   (1.0,  [ 2, 1,-1, 0,-2, 0, 0, 0, 3]), 	# ohm (V/A)
        'S':     (1.0,  [-2,-1, 1, 0, 2, 0, 0, 0,-3]), 	# siemens (Ohm-1)
        'Wb':    (1.0,  [ 2, 1,-1, 0,-1, 0, 0, 0, 3]), 	# weber (V.s)
        'T':     (1.0,  [ 0, 1,-1, 0,-1, 0, 0, 0, 3]), 	# tesla (Wb/m2)
        'H':     (1.0,  [ 2, 1, 0, 0,-2, 0, 0, 0, 3]),  # henry (Wb/A)
        'lm':    (1.0,  [ 0, 0, 0, 0, 0, 1, 0, 2, 0]), 	# lumen (cd.sr)
        'lx':    (1.0,  [-2, 0, 0, 0, 0, 1, 0, 2, 0]), 	# lux (lm/m2)
        'Bq':    (1.0,  [ 0, 0,-1, 0, 0, 0, 0, 0, 0]), 	# becquerel (s-1)
        'Gy':    (1.0,  [ 2, 0,-2, 0, 0, 0, 0, 0, 0]), 	# gray (J/kg)
        'Sv':    (1.0,  [ 2, 0,-2, 0, 0, 0, 0, 0, 0]), 	# sivert (J/kg)
        # CGS units                          
        'dyn':   (1.0,  [ 1, 1,-2, 0, 0, 0, 0, 0,-2]),     # dyne (g.cm/s2)
        'erg':   (1.0,  [ 2, 1,-2, 0, 0, 0, 0, 0,-4]),     # erg (dyn.cm)
        'G':     (1.0,  [ 0, 1,-1, 0,-1, 0, 0, 0,-1]),     # Gauss (10*-4.T)
    }
    prefixes = {  
        'Y':    (1.0, [0,0,0,0,0,0,0,0, 24]),  # yotta
        'Z':    (1.0, [0,0,0,0,0,0,0,0, 21]),  # zetta
        'E':    (1.0, [0,0,0,0,0,0,0,0, 18]),  # exa
        'P':    (1.0, [0,0,0,0,0,0,0,0, 15]),  # peta
        'T':    (1.0, [0,0,0,0,0,0,0,0, 12]),  # tera
        'G':    (1.0, [0,0,0,0,0,0,0,0,  9]),  # giga
        'M':    (1.0, [0,0,0,0,0,0,0,0,  6]),  # mega
        'k':    (1.0, [0,0,0,0,0,0,0,0,  3]),  # kilo
        'h':    (1.0, [0,0,0,0,0,0,0,0,  2]),  # hectoh
        'da':   (1.0, [0,0,0,0,0,0,0,0,  1]),  # deka
        'd':    (1.0, [0,0,0,0,0,0,0,0, -1]),  # deci
        'c':    (1.0, [0,0,0,0,0,0,0,0, -2]),  # centi
        'm':    (1.0, [0,0,0,0,0,0,0,0, -3]),  # milli
        'u':    (1.0, [0,0,0,0,0,0,0,0, -6]),  # micro
        'n':    (1.0, [0,0,0,0,0,0,0,0, -9]),  # nano
        'p':    (1.0, [0,0,0,0,0,0,0,0,-12]),  # pico
        'f':    (1.0, [0,0,0,0,0,0,0,0,-15]),  # femto
        'a':    (1.0, [0,0,0,0,0,0,0,0,-18]),  # atto
        'z':    (1.0, [0,0,0,0,0,0,0,0,-21]),  # zepto
        'y':    (1.0, [0,0,0,0,0,0,0,0,-24]),  # yocto
    }
    numbers = {  
        '[pi]':    (np.pi,     [0,0,0,0,0,0,0,0, 0]),  # pi
        '[euler]': (np.e,      [0,0,0,0,0,0,0,0, 0]),  # euler's number
        '[N_A]':   (6.0221367, [0,0,0,0,0,0,0,0,23]),  # avogadro's number
        '%':       (1.0,       [0,0,0,0,0,0,0,0,-2]),  # percent
    }
    other = {
        'Cel':   (1.0,  [0, 0, 0, 1, 0, 0, 0, 0, 0]), 	# degree (cel(1 K))
    }

    def __init__(self):
        self.nbase = len(self.base)
        self.units = self.base | self.derivates

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        pass
    
    def equal(self, unit1, unit2):
        if unit1[0]!=unit2[0]:
            return False
        if unit1[1]!=unit2[1]:
            return False
        return True
    
    def multiply(self, unit1, unit2):
        num = unit1[0]*unit2[0]
        base = [unit1[1][i]+unit2[1][i] for i in range(self.nbase)]
        return (num, base)

    def divide(self, unit1, unit2):
        num = unit1[0]/unit2[0]
        base = [unit1[1][i]-unit2[1][i] for i in range(self.nbase)]
        return (num, base)

    def power(self, unit, power):
        num = unit[0]**power
        base = [unit[1][i]*power for i in range(self.nbase)]
        return (num, base)

    def unit(self, unit):
        unit_bak = unit
        exp, base, prefix = '', '', ''
        symbol, unit = unit[-1], ' '+unit[:-1]
        # parse exponent
        while len(unit):
            if not re.match('^[0-9+-]{1}$', symbol):
                break
            exp = symbol+exp
            symbol, unit = unit[-1], unit[:-1]
        # parse unit symbol
        unitkeys = self.units.keys()
        while len(unit):
            nbase = len(base)+1
            ukeys = [key[-nbase:] for key in unitkeys]
            if symbol+base not in ukeys:
                break
            base = symbol+base
            symbol, unit = unit[-1], unit[:-1]
        # parse unit prefix
        while len(unit):
            prefix = symbol+prefix
            symbol, unit = unit[-1], unit[:-1]
            if symbol==' ':
                break
        if prefix:
            if prefix not in self.prefixes.keys():
                raise Exception(f"Unit prefix '{prefix}' is not available in: {unit_bak}")
            unit = self.multiply(self.prefixes[prefix],self.units[base])
        else:
            unit = self.units[base]
        if exp:
            unit = self.power(unit,int(exp))
        #print("%-06s"%unit_bak, "%-03s"%prefix, "%-03s"%base, "%03s"%exp, unit)
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
            if symbol=='.':
                return self.multiply(
                    self.expression(part1, expr_bak),
                    self.expression(part2, expr_bak)
                )
            elif symbol=='/':
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
    
