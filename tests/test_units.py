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
        print(f"Base: {unit.num} {unit.base}")
        assert p.equal(unit, PUML_Unit(1.0, [1 for i in range(p.nbase)]))

def test_operations():
    with PUML_Parse() as p:
        # Multiplication
        unit1 = PUML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        unit2 = PUML_Unit(2.0, [i for i in range(2,2+p.nbase)])
        unit3 = p.multiply(unit1, unit2)
        unit4 = PUML_Unit(unit1.num*unit2.num,
                          [unit1.base[i]+unit2.base[i] for i in range(p.nbase)])
        print(f"  {unit1.num} {unit1.base}\n* {unit2.num} {unit2.base}\n= {unit3.num} {unit3.base}\n")
        assert p.equal(unit3, unit4)
        # Division
        unit1 = PUML_Unit(4.0, [i+i for i in range(1,1+p.nbase)])
        unit2 = PUML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        unit3 = p.divide(unit1, unit2)
        unit4 = PUML_Unit(unit1.num/unit2.num,
                          [unit1.base[i]-unit2.base[i] for i in range(p.nbase)])
        print(f"  {unit1.num} {unit1.base}\n/ {unit2.num} {unit2.base}\n= {unit3.num} {unit3.base}\n")
        assert p.equal(unit3, unit4)
        # Power
        unit1 = PUML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        power = 3
        unit2 = p.power(unit1, power)
        unit3 = PUML_Unit(unit1.num**power, [unit1.base[i]*power for i in range(p.nbase)])
        print(f"  {unit1.num} {unit1.base}\n^ {power}\n= {unit3.num} {unit3.base}")
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
            print("%-05s"%name, f"{unit1.num} {unit1.base}")
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
            print("%-03s %-15s"%(name,expr), "%.03e"%unit1.num, unit1.base)
            assert p.equal(unit1, unit2)        

def test_derivates():
    # Check if derived units are correct
    with PUML_Parse() as p:
        for sign, unit in p.derivates.items():
            if not unit.definition:
                continue
            expr = p.expression(unit.definition)
            print("%-13s"%unit.name, "%-3s"%sign, "%-12s"%unit.definition,
                  "%.03e"%expr.num, expr.base)
            assert p.equal(expr, unit)            
            
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
            
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
