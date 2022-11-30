import sys
sys.path.insert(1, '/Users/perseus/Projects/pics/src')
from PUML_Parse import *
import pytest
import numpy as np

def test_operations():
    with PUML_Parse() as p:
        unit1 = (2.0, [i for i in range(1,9)])
        unit2 = (2.0, [i for i in range(2,10)])
        unit3 = p.multiply(unit1, unit2)
        unit4 = (unit1[0]*unit2[0], [unit1[1][i]+unit2[1][i] for i in range(8)])
        print(' ',unit1,'\n*',unit2,'\n=',unit3,'\n')
        assert p.equal(unit3, unit4)

        unit1 = (4.0, [i+i for i in range(1,9)])
        unit2 = (2.0, [i for i in range(1,9)])
        unit3 = p.divide(unit1, unit2)
        unit4 = (unit1[0]/unit2[0], [unit1[1][i]-unit2[1][i] for i in range(8)])
        print(' ',unit1,'\n/',unit2,'\n=',unit3,'\n')
        assert p.equal(unit3, unit4)

        unit1 = (2.0, [i for i in range(1,9)])
        power = 3
        unit2 = p.power(unit1, power)
        unit3 = (unit1[0]**power, [unit1[1][i]*power for i in range(8)])
        print(' ',unit1,'\n^',power,'\n=',unit3)
        assert p.equal(unit2, unit3)
        
def test_units():
    with PUML_Parse() as p:
        units = {
            'm':     p.units['m'],
            'm-2':   p.power(p.units['m'],-2),
            'mm':    p.multiply(p.prefixes['m'], p.units['m']),
            'km2':   p.power(p.multiply(p.prefixes['k'], p.units['m']), 2),
            'uOhm3': p.power(p.multiply(p.prefixes['u'], p.units['Ohm']), 3),
        }
        for name, unit2 in units.items():
            unit1 = p.unit(name)
            print("%-05s"%name, unit1)
            assert p.equal(unit1, unit2)            

def test_expressions():
    with PUML_Parse() as p:
        newton = p.multiply(p.prefixes['k'],p.base['g'])
        newton = p.multiply(newton,p.base['m'])
        newton = p.divide(newton,p.power(p.base['s'],2))
        assert p.equal(newton, p.units['N'])
        print('N=kg.m/s2',newton)
        
        #p.expression('km2/W')
        #p.expression('MJ.s')
        #print(p.expression('kg.m.s-2'))
        #print(p.expression('kg.m/s2'))
        #print(p.expression('(kg.(m))/(s2)'))
        #p.expression('kg.m2/s2')
        pass

def test_derived_si():
    units = {
        'sr':  'rad2',
        'Hz':  's-1',
        'N':   'kg.m/s2',
        'Pa':  'N/m2',
        'J':   'N.m',
        'W':   'J/s',
        'A':   'C/s',
        'V':   'J/C',
        'F':   'C/V',
        'Ohm': 'V/A',
        'S':   'Ohm-1',
        'Wb':  'V.s',
        'T':   'Wb/m2',
        'H':   'Wb/A',
        'lm':  'cd.sr',
        'lx':  'lm/m2',
        'Bq':  's-1',
        'Gy':  'J/kg',
        'Sv':  'J/kg',
    }
    with PUML_Parse() as p:
        for name, expr in units.items():
            unit1 = p.expression(expr)
            unit2 = p.units[name]
            print("%-03s"%name, unit1)
            assert p.equal(unit1, unit2)            
            
def test_derived_cgs():
    units = {
        'dyn': 'g.cm/s2',
        'erg': 'dyn.cm',
        'G':   '10*-4.T',
    }
    with PUML_Parse() as p:
        for name, expr in units.items():
            unit1 = p.expression(expr)
            unit2 = p.units[name]
            print("%-03s"%name, unit1)
            assert p.equal(unit1, unit2)            

if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
