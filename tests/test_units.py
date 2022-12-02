import sys
sys.path.insert(1, '/Users/perseus/Projects/pics/src')
from PUML_Parse import *
import pytest
import numpy as np

def test_base():
    with PUML_Parse() as p:
        # Closure of base units
        unit = PUML_Unit(1.0, [0 for i in range(p.nbase)])
        for base in p.base.values():
            unit = p.multiply(unit,base)
        print('Base:',unit)
        assert p.equal(unit, PUML_Unit(1.0, [1 for i in range(p.nbase)]))

def test_operations():
    with PUML_Parse() as p:
        # Multiplication
        unit1 = PUML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        unit2 = PUML_Unit(2.0, [i for i in range(2,2+p.nbase)])
        unit3 = p.multiply(unit1, unit2)
        unit4 = PUML_Unit(unit1[0]*unit2[0], [unit1[1][i]+unit2[1][i] for i in range(p.nbase)])
        print(' ',unit1,'\n*',unit2,'\n=',unit3,'\n')
        assert p.equal(unit3, unit4)
        # Division
        unit1 = PUML_Unit(4.0, [i+i for i in range(1,1+p.nbase)])
        unit2 = PUML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        unit3 = p.divide(unit1, unit2)
        unit4 = PUML_Unit(unit1[0]/unit2[0], [unit1[1][i]-unit2[1][i] for i in range(p.nbase)])
        print(' ',unit1,'\n/',unit2,'\n=',unit3,'\n')
        assert p.equal(unit3, unit4)
        # Power
        unit1 = PUML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        power = 3
        unit2 = p.power(unit1, power)
        unit3 = PUML_Unit(unit1[0]**power, [unit1[1][i]*power for i in range(p.nbase)])
        print(' ',unit1,'\n^',power,'\n=',unit3)
        assert p.equal(unit2, unit3)
        
def test_units():
    with PUML_Parse() as p:
        units = {
            'm':     p.units['m'],                               # just a unit                      
            'm-2':   p.power(p.units['m'],-2),                   # exponents
            'mm':    p.multiply(p.prefixes['m'], p.units['m']),  # prefixes
            'km2':   p.power(                                    # all together
                p.multiply(p.prefixes['k'], p.units['m']),
                2
            ),
            'uOhm3': p.power(                                    # units with long names
                p.multiply(p.prefixes['u'],p.units['Ohm']),
                3
            ),
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
        units = {
            'N':   'kg.m/s2',        # basic operations
            'Pa':  'kg/(s2.m)',      # parentheses in denominator
            'J':   '(kg.m2)/s2',     # parentheses in nominator
            'W':   'kg.(m2/s3)',     # fraction in parentheses
            'A':   'C.s-1',          # negative exponents
            'V':   'kg.(m2/(s2.C))', # nested parentheses
            'Ohm': '((kg.m2)/s)/C2', # multiple fractions with parentheses
            'S':   's.C2/kg/m2',     # multiple fractions without parentheses
            'deg': 'rad.180/[pi]',   # numbers and constants
        }
        for name, expr in units.items():
            unit1 = p.units[name]
            unit2 = p.expression(expr)
            print("%-03s %-15s"%(name,expr), unit1)
            assert p.equal(unit1, unit2)        

def test_derivates():
    # Check if derived units are correct
    with PUML_Parse() as p:
        for sign, unit in p.derivates.items():
            if not unit.definition:
                continue
            expr = p.expression(unit.definition)
            print("%-13s"%unit.name, "%-3s"%sign, "%-12s"%unit.definition, expr)
            assert p.equal(expr, unit)            
            
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

def test_convert():
    examples = [
        (1, 'm',   1e-3,              'km'),
        (1, 'kJ',  1e3,               'J'),
        (1, 'eV',  1.60217733e-4,     'fJ'),
        (1, 'erg', 624.1506363094028, 'GeV'),
    ]
    with PUML_Parse() as p:
        for e in examples:
            print(f"{e[0]} {e[1]:4s} = {e[2]:.4f} {e[3]}")
            assert p.convert(e[0], e[1], e[3]) == e[2]

        print(p.expression('rad.180/[pi]'))
            
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
