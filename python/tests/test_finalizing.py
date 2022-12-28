import sys, os
import pytest
import numpy as np

sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'src'))
from ParseDPML import *

def parse(code):
    with ParseDPML(code) as p:
        p.initialize()
        p.finalize()
        p.display()
        return p.data()

def test_hierarchy():
    data = parse('''
general.colonel int = 1  # namespace notation
  captain                # group nodes
     soldier int = 2     # lowest node in the hierarchy
    ''')
    np.testing.assert_equal(data,{
        'general.colonel': 1,
        'general.colonel.captain.soldier': 2
    })

def test_modification():
    data = parse('''
size float = 70 cm    # definition
size float = 80 cm    # modifications of value
size = 90 cm          # omitting datatype
size = 100            # omitting units
size = 1 m            # using different prefix

energy float = 1.23 J # definition
energy = 2.2 erg      # switching from SI to cgs
energy = 2.2 g*cm2/s2 # using unit expressions

angle float = 1.57079633 rad  # definition in radians
angle = 31 '                  # angle minutes

alcohol float = 34 %  # definition
alcohol = 2 [ppth]    # converting dimensionless units

temp float = 20 Cel
temp = 280.15 K
    ''')
    np.testing.assert_equal(data,{
        'size':   100,
        'energy': 2.2e-7,
        'angle':  0.0090175342,
        'alcohol': 0.2,
        'temp': 7,
    })  
    with pytest.raises(Exception) as e_info:
        parse('''
age int = 34 a
age float = 55
        ''')
    assert e_info.value.args[0] == "Datatype <class 'int'> of node 'age' cannot be changed to <class 'float'>"
    with pytest.raises(Exception) as e_info:
        parse('''
weight = 23 kg
        ''')
    assert e_info.value.args[0] == "Modifying undefined node:"
    assert e_info.value.args[1] == "weight"

def test_option_units():
    data = parse("""
width float = 2 m
  = 2 m
  = 3 m
width = 3000 mm
    """)
    np.testing.assert_equal(data,{
        'width': 3.0
    })
    with pytest.raises(Exception) as e_info:
        parse('''
size float = 24 cm
  = 24 cm
  = 25 m
size = 25 cm
        ''')
    assert e_info.value.args[0] == "Value '25.0' of node 'size' doesn't match with any option:"
    assert e_info.value.args[1] == [None, 24.0, 2500.0]
    
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
