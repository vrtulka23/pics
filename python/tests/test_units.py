import sys, os
import pytest
import numpy as np

sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'src'))
from PPML_Converter import *

def test_base():
    with PPML_Converter() as p:
        # Closure of base units
        unit = PPML_Unit(1.0, [0 for i in range(p.nbase)])
        for base in p.base.values():
            unit = p.multiply(unit,base)
        print(f"Base: {unit.num} {unit.base}")
        assert p.equal(unit, PPML_Unit(1.0, [1 for i in range(p.nbase)]))

def test_operations():
    with PPML_Converter() as p:
        # Multiplication
        unit1 = PPML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        unit2 = PPML_Unit(2.0, [i for i in range(2,2+p.nbase)])
        unit3 = p.multiply(unit1, unit2)
        unit4 = PPML_Unit(unit1.num*unit2.num,
                          [unit1.base[i]+unit2.base[i] for i in range(p.nbase)])
        print(f"  {unit1.num} {unit1.base}\n* {unit2.num} {unit2.base}\n= {unit3.num} {unit3.base}\n")
        assert p.equal(unit3, unit4)
        # Division
        unit1 = PPML_Unit(4.0, [i+i for i in range(1,1+p.nbase)])
        unit2 = PPML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        unit3 = p.divide(unit1, unit2)
        unit4 = PPML_Unit(unit1.num/unit2.num,
                          [unit1.base[i]-unit2.base[i] for i in range(p.nbase)])
        print(f"  {unit1.num} {unit1.base}\n/ {unit2.num} {unit2.base}\n= {unit3.num} {unit3.base}\n")
        assert p.equal(unit3, unit4)
        # Power
        unit1 = PPML_Unit(2.0, [i for i in range(1,1+p.nbase)])
        power = 3
        unit2 = p.power(unit1, power)
        unit3 = PPML_Unit(unit1.num**power, [unit1.base[i]*power for i in range(p.nbase)])
        print(f"  {unit1.num} {unit1.base}\n^ {power}\n= {unit3.num} {unit3.base}")
        assert p.equal(unit2, unit3)
        
def test_units():
    with PPML_Converter() as p:
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
            '[pi]':  p.units['[pi]'],                            # number pi
            '[e]':   p.units['[e]'],                             # electronvolt
        }
        for name, unit2 in units.items():
            unit1 = p.unit(name)
            print("%-05s"%name, f"{unit1.num:.03e} {unit1.base}")
            assert p.equal(unit1, unit2)            

def test_expressions():
    with PPML_Converter() as p:
        newton = p.multiply(p.prefixes['k'],p.base['g'])
        newton = p.multiply(newton,p.base['m'])
        newton = p.divide(newton,p.power(p.base['s'],2))
        units = {
            'N':   'kg*m/s2',        # basic operations
            'Pa':  'kg/(s2*m)',      # parentheses in denominator
            'J':   '(kg*m2)/s2',     # parentheses in nominator
            'W':   'kg*(m2/s3)',     # fraction in parentheses
            'A':   'C*s-1',          # negative exponents
            'V':   'kg*(m2/(s2*C))', # nested parentheses
            'Ohm': '((kg*m2)/s)/C2', # multiple fractions with parentheses
            'S':   's*C2/kg/m2',     # multiple fractions without parentheses
            'deg': '2*[pi]*rad/360', # numbers and constants
        }
        for name, expr in units.items():
            unit1 = p.units[name]
            unit2 = p.expression(expr)
            print("%-03s %-15s"%(name,expr), "%.03e"%unit1.num, unit1.base)
            assert p.equal(unit1, unit2)        

def test_derivates():
    # Check if derived units are correct
    with PPML_Converter() as p:
        for sign, unit in p.derivates.items():
            if not unit.dfn:
                continue
            expr = p.expression(unit.dfn)
            print("%-13s"%unit.name, "%-4s"%sign, "%-15s"%unit.dfn,
                  "%.06f"%expr.num, expr.base)
            equal = p.equal(expr, unit)
            if not equal:
                print(f"Expr.: {expr.num:.6f} {expr.base}")
                print(f"Unit:  {unit.num:.6f} {unit.base}")
            assert equal
            
def test_convert():
    examples = [
        (1,   'm',    1e-3,          'km'),
        (1,   'kJ',   1e3,           'J'),
        (1,   'eV',   1.6021773e-4,  'fJ'),
        (1,   'erg',  624.150636,    'GeV'),
        (1,   'deg',  0.01745329,    'rad'),
        (1,   'Cel',  274.15,        'K'),
        (1,   'kCel', 1273.15,       'K'),
        (1e3, 'K',    726.85,        'Cel'),
        (1,   'kK',   0.72685,       'kCel'),
    ]
    with PPML_Converter() as p:
        for (value1,expr1,value2,expr2) in examples:
            print(f"{value1:.3e} {expr1:4s} = {value2:.3e} {expr2}")
            conv = p.convert(value1, expr1, expr2)
            equal = isclose(conv, value2, rel_tol=1e-6)
            if not equal:
                print(f"Value 1 given:     {value1:.3e} {expr1}")
                print(f"Value 2 converted: {conv} {expr2}")
                print(f"Value 2 expected:  {value2} {expr2}")
            assert equal
            
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
