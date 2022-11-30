from pydantic import BaseModel
import numpy as np

class PUML_Parse:

    base = {
        '10*':  (1, [1,0,0,0,0,0,0,0]),  # 1
        'm':    (1, [0,1,0,0,0,0,0,0]),  # 2
        'g':    (1, [0,0,1,0,0,0,0,0]),  # 3
        's':    (1, [0,0,0,1,0,0,0,0]),  # 4
        'rad':  (1, [0,0,0,0,1,0,0,0]),  # 5
        'K':    (1, [0,0,0,0,0,1,0,0]),  # 6
        'C':    (1, [0,0,0,0,0,0,1,0]),  # 7
        'cd':   (1, [0,0,0,0,0,0,0,1]),  # 8
    }
    derivates = { # 10,m,g,s,rad,K,C,cd
        'sr':    (1,  [ 0, 0, 0, 0, 2,0, 0,0]), 	# steradian (rad2)
        'Hz':    (1,  [ 0, 0, 0,-1, 0,0, 0,0]), 	# hertz (s-1)
        'N':     (1,  [ 3, 1, 1,-2, 0,0, 0,0]), 	# newton (kg.m/s2)
        'Pa':    (1,  [ 3,-1, 1,-2, 0,0, 0,0]), 	# pascal (N/m2)
        'J':     (1,  [ 3, 2, 1,-2, 0,0, 0,0]), 	# joule (N.m)
        'W':     (1,  [ 3, 2, 1,-3, 0,0, 0,0]), 	# watt (J/s)
        'A':     (1,  [ 0, 0, 0,-1, 0,0, 1,0]), 	# ampere (C/s)
        'V':     (1,  [ 3, 2, 1,-2, 0,0,-1,0]), 	# volt (J/C)
        'F':     (1,  [-3,-2,-1, 2, 0,0, 1,0]), 	# farad (C/V)
        'Ohm':   (1,  [ 3, 2, 1, 0, 0,0,-1,0]), 	# ohm (V/A)
        'S':     (1,  [-3,-2,-1, 0, 0,0, 1,0]), 	# siemens (Ohm-1)
        'Wb':    (1,  [ 3, 2, 1,-1, 0,0,-1,0]), 	# weber (V.s)
        'T':     (1,  [ 3, 0, 1,-1, 0,0,-1,0]), 	# tesla (Wb/m2)
        'H':     (1,  [ 3, 2, 1, 0, 0,0,-2,0]),         # henry (Wb/A)
        'lm':    (1,  [ 0, 0, 0, 0, 2,0, 0,1]), 	# lumen (cd.sr)
        'lx':    (1,  [ 0,-2, 0, 0, 2,0, 0,1]), 	# lux (lm/m2)
        'Bq':    (1,  [ 0, 0, 0,-1, 0,0, 0,0]), 	# becquerel (s-1)
        'Gy':    (1,  [ 0, 2, 0,-2, 0,0, 0,0]), 	# gray (J/kg)
        'Sv':    (1,  [ 0, 2, 0,-2, 0,0, 0,0]), 	# sivert (J/kg)
    }
    prefixes = {  # 10,m,g,s,rad,K,C,cd
        'Y':    (1, [24, 0,0,0,0,0,0,0]),  # yotta
        'Z':    (1, [21, 0,0,0,0,0,0,0]),  # zetta
        'E':    (1, [18, 0,0,0,0,0,0,0]),  # exa
        'P':    (1, [15, 0,0,0,0,0,0,0]),  # peta
        'T':    (1, [12, 0,0,0,0,0,0,0]),  # tera
        'G':    (1, [9,  0,0,0,0,0,0,0]),  # giga
        'M':    (1, [6,  0,0,0,0,0,0,0]),  # mega
        'k':    (1, [3,  0,0,0,0,0,0,0]),  # kilo
        'h':    (1, [2,  0,0,0,0,0,0,0]),  # hectoh
        'da':   (1, [1,  0,0,0,0,0,0,0]),  # deka
        'd':    (1, [-1, 0,0,0,0,0,0,0]),  # deci
        'c':    (1, [-2, 0,0,0,0,0,0,0]),  # centi
        'm':    (1, [-3, 0,0,0,0,0,0,0]),  # milli
        'u':    (1, [-6, 0,0,0,0,0,0,0]),  # micro
        'n':    (1, [-9, 0,0,0,0,0,0,0]),  # nano
        'p':    (1, [-12,0,0,0,0,0,0,0]),  # pico
        'f':    (1, [-15,0,0,0,0,0,0,0]),  # femto
        'a':    (1, [-18,0,0,0,0,0,0,0]),  # atto
        'z':    (1, [-21,0,0,0,0,0,0,0]),  # zepto
        'y':    (1, [-24,0,0,0,0,0,0,0]),  # yocto
    }
    numbers = {  # 10,m,g,s,rad,K,C,cd
        '[pi]':    (np.pi,     [ 0, 0,0,0,0,0,0,0]),  # pi
        '[euler]': (np.e,      [ 0, 0,0,0,0,0,0,0]),  # euler's number
        '[N_A]':   (6.0221367, [23, 0,0,0,0,0,0,0]),  # avogadro's number
        'mol':     (6.0221367, [23, 0,0,0,0,0,0,0]),  # mole
        '%':       (1,         [-2, 0,0,0,0,0,0,0]),  # percent
    }
    other = {
        'Cel':   (1,  [ 0, 0, 0, 0, 0,1, 0,0]), 	# degree (cel(1 K))
    }

    def __init__(self, line):
        self.nbase = len(self.base)
        self.units = self.base | self.derivates
        
        if line.count('(')!=line.count(')'):
            raise Exception(f"Unclosed parenthesis in: {line}")
        print(line)
        self.parse(line)

    def times(self, unit1, unit2):
        num = unit1[0]*unit2[0]
        base = [unit1[1][i]+unit2[1][i] for i in range(self.nbase)]
        return (num, base)

    def divided(self, unit1, unit2):
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
        unitkeys = self.units.keys()
        while len(unit):
            if symbol.isnumeric() or symbol in ['-','+']:
                exp = symbol+exp
            else:
                nbase = len(base)+1
                ukeys = [key[-nbase:] for key in unitkeys]
                if symbol+base in ukeys and not prefix:
                    base = symbol+base
                else:
                    prefix = symbol+prefix
            symbol, unit = unit[-1], unit[:-1]
        if prefix:
            if prefix not in self.prefixes.keys():
                raise Exception(f"Unit prefix '{prefix}' is not available in: {unit_bak}")
            unit = self.times(self.prefixes[prefix],self.units[base])
        else:
            unit = self.units[base]
        if exp:
            unit = self.power(unit,int(exp))
        print(prefix, base, exp, unit)        
    
    def parse(self, line):
        
        newton = self.times(self.prefixes['k'],self.base['g'])
        newton = self.times(newton,self.base['m'])
        newton = self.divided(newton,self.power(self.base['s'],2))
        print('newton',newton)

        self.unit('km-2')
        self.unit('MW')
        self.unit('s2')
        self.unit('Ohm')
