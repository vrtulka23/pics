import sys, os
import pytest
import numpy as np

sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'src'))
from DPML import *

def test_or_and():
    with DPML() as p:
        assert p.expression('true || true || true')    == True
        assert p.expression('false || true || false')  == True
        assert p.expression('false || false || false') == False
        assert p.expression('true && true && true')    == True
        assert p.expression('true && false && true')   == False
        assert p.expression('false && false && false') == False
        assert p.expression('true && true && true || false || false') == True
        assert p.expression('false || true && false && true || true') == True
        assert p.expression('false || false || true && false && true') == False

def test_parenthesis():
    with DPML() as p:
        assert p.expression('(true || false) && true && true') == True
        assert p.expression('true && (true && false) && true') == False
        assert p.expression('false || false || (true || false)') == True
        assert p.expression('false || (true || false) && true') == True
        assert p.expression('false || true && (false || false)') == False
        assert p.expression('false || ((false||true) || false) && (true||false)') == True

def test_compare_nodes():
    code = """
    dogs int = 23
    cats int = 44
    birds int = 23
    fish int = 12
    animal bool = true
    """
    with DPML(code) as p:
        p.initialize()
        # node pair comparison
        assert p.expression('{?dogs} == {?cats}') == False
        assert p.expression('{?dogs} == {?birds}') == True
        assert p.expression('{?dogs} != {?cats}') == True
        assert p.expression('{?dogs} != {?birds}') == False
        assert p.expression('{?dogs} <= {?cats}') == True
        assert p.expression('{?dogs} <= {?birds}') == True
        assert p.expression('{?dogs} <= {?fish}') == False
        assert p.expression('{?dogs} >= {?cats}') == False
        assert p.expression('{?dogs} >= {?birds}') == True
        assert p.expression('{?dogs} >= {?fish}') == True
        assert p.expression('{?dogs} <  {?cats}') == True
        assert p.expression('{?dogs} <  {?fish}') == False
        assert p.expression('{?dogs} >  {?fish}') == True
        assert p.expression('{?dogs} >  {?cats}') == False
        # single bool node
        assert p.expression('{?animal}') == True
        assert p.expression('~{?animal}') == False   # negated value
        # is node defined
        assert p.expression('!{?dogs}') == True
        assert p.expression('!{?elefant}') == False
        assert p.expression('!{?elefant} == false') == True
        assert p.expression('~!{?elefant}') == True  # negated value

def test_compare_values():
    code = """
    weight float = 57.3 kg
    """
    with DPML(code) as p:
        p.initialize()
        # comparison with the same units
        assert p.expression('{?weight} == 57.30 kg') == True
        assert p.expression('{?weight} == 57.31 kg') == False
        assert p.expression('{?weight} != 57.30 kg') == False
        assert p.expression('{?weight} != 57.31 kg') == True
        assert p.expression('{?weight} <= 57.30 kg') == True
        assert p.expression('{?weight} <= 60 kg') == True
        assert p.expression('{?weight} <= 50 kg') == False
        # comparison with different units
        assert p.expression('{?weight} >= 57300 g') == True
        assert p.expression('{?weight} >= 50000 g') == True
        assert p.expression('{?weight} >= 60000 g') == False
        assert p.expression('{?weight} > 50000 g') == True
        assert p.expression('{?weight} > 60000 g') == False
        # comparison without specifying units
        assert p.expression('{?weight} < 50') == False
        assert p.expression('{?weight} < 60') == True

def test_combination():
    code = """
    size float = 34 cm
    geometry int = 2
      = 1 # line
      = 2 # square
      = 3 # cube
    filled bool = true
    dimension int = 2
    """
    with DPML(code) as p:
        p.initialize()
        assert p.expression("""
        {?size} > 30 cm 
        || ({?size} < 0.4 m || {?size} >= 34) 
        && ({?geometry} == 1 && {?geometry}<={?dimension})
        && {?filled}
        || ~!{?color}
        """) == True
        
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
