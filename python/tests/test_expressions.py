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

def test_comparison():
    code = """
    dogs int = 23
    cats int = 44
    birds int = 23
    fish int = 12
    """
    with DPML(code) as p:
        p.initialize()
        # node pair comparison
        assert p.expression('{?dogs}=={?cats}') == False
        assert p.expression('{?dogs}=={?birds}') == True
        assert p.expression('{?dogs}!={?cats}') == True
        assert p.expression('{?dogs}!={?birds}') == False
        assert p.expression('{?dogs}<={?cats}') == True
        assert p.expression('{?dogs}<={?birds}') == True
        assert p.expression('{?dogs}<={?fish}') == False
        assert p.expression('{?dogs}>={?cats}') == False
        assert p.expression('{?dogs}>={?birds}') == True
        assert p.expression('{?dogs}>={?fish}') == True
        assert p.expression('{?dogs}<{?cats}') == True
        assert p.expression('{?dogs}<{?fish}') == False
        assert p.expression('{?dogs}>{?fish}') == True
        assert p.expression('{?dogs}>{?cats}') == False
        # single node comparison
        assert p.expression('!{?dogs}') == True
        assert p.expression('!{?elefant}') == False
        assert p.expression('!{?elefant}==false') == True
        
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
