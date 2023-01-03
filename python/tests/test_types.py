import sys, os
import pytest
import numpy as np

sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'src'))
from DPML import *

def parse(code):
    with DPML(code) as p:
        p.initialize()
        p.display()
        return p.data()

def test_name():
    data = parse('''
very-long.node23_NAME int = 1
    ''')
    np.testing.assert_equal(data,{
        'very-long.node23_NAME': 1,
    })
    with pytest.raises(Exception) as e_info:
        parse('wrong$name int = 3')
    assert e_info.value.args[0] == "Name has an invalid format: wrong$name int = 3"
    
def test_types():
    data = parse('''
adult bool = true
age int = 20 a
weight float = 63.3 kg
name str = 'Laura'
    ''')
    np.testing.assert_equal(data,{
        'adult': True,
        'age': 20,
        'weight': 63.3,
        'name': 'Laura'
    })

def test_options():
    data = parse('''
coordinates int = 1
  = 1  # linear
  = 2  # cylindrical
  = 3  # spherical
assets str = none
  = house
  = car
    ''')
    np.testing.assert_equal(data,{
        'coordinates': 1,
        'assets': None
    })
    with pytest.raises(Exception) as e_info:
        parse("""
length float! = none cm
  = 12 cm
  = 34 cm
        """)
    assert e_info.value.args[0] == "Value of node 'length' must be defined"
    with pytest.raises(Exception) as e_info:
        parse("""
deposition bool = true
  = true
  = false
        """)
    assert e_info.value.args[0] == "Node 'bool' does not support options"
    
def test_dimensions():
    data = parse('''
counts int[3] = [4234,34,2]
lengths float[2:][2] = [[4234,34],[234,34]] cm
colleagues str[:] = ["John","Patricia","Lena"]
logic bool[2] = [true,false]
    ''')
    np.testing.assert_equal(data,{
        'counts': np.array([4234,   34,    2]),
        'lengths': np.array([[4234.,   34.],[ 234.,   34.]]),
        'colleagues': np.array(['John', 'Patricia', 'Lena'], dtype='<U8'),
        'logic': np.array([ True, False])
    })
    with pytest.raises(Exception) as e_info:
        parse('counts int[2] = [4234,34,2]')
    assert e_info.value.args[0] == "Node 'counts' has invalid dimension: dim(0)=3 > 2"
    with pytest.raises(Exception) as e_info:
        parse('counts int[2] = [4234]')
    assert e_info.value.args[0] == "Node 'counts' has invalid dimension: dim(0)=1 < 2"
    with pytest.raises(Exception) as e_info:
        parse('counts int[:2] = [4234,34,2]')
    assert e_info.value.args[0] == "Node 'counts' has invalid dimension: dim(0)=3 > 2"
    with pytest.raises(Exception) as e_info:
        parse('counts int[2:] = [4234]')
    assert e_info.value.args[0] == "Node 'counts' has invalid dimension: dim(0)=1 < 2"
    with pytest.raises(Exception) as e_info:
        parse('counts int[2][3:] = [[234,4234],[234,34]]')
    assert e_info.value.args[0] == "Node 'counts' has invalid dimension: dim(1)=2 < 3"

def test_defined():
    data = parse('''
debts bool = None
children int! = 3
''')
    np.testing.assert_equal(data,{
        'debts': None,
        'children': 3
    })
    with pytest.raises(Exception) as e_info:
        parse('counts int! = none')
    assert e_info.value.args[0] == "Value of node 'counts' must be defined"

def test_strings():
    data = parse('''
country str = Canada              # strings without whitespace
name str = "Johannes Brahms"      # strings with a whitespace
counts int[3] = "[0, 1, 2]"       # arrays with whitespaces between items
answers bool[2] = "[true, false]" 
names str[2] = '["Jolana", "Anastasia"]'
girl_friend str = "\"l'amie\""    # escaping of double quotes
boy_friend str = '"l\'ami"'       # escaping of single quotes
hashtag str = '#nocomment'        # comment
anticommutator str = '{a,b}'      # this is not an import
    ''')
    np.testing.assert_equal(data,{
        'country': 'Canada',
        'name': 'Johannes Brahms',
        'counts': np.array([0, 1, 2]),
        'answers': np.array([ True, False]),
        'names': np.array(['Jolana', 'Anastasia'], dtype='<U9'),
        'girl_friend': '"l\'amie"',
        'boy_friend': '"l\'ami"',
        'hashtag': '#nocomment',
        'anticommutator': '{a,b}'
      })
    with pytest.raises(Exception) as e_info:
        parse('name str = Johannes Brahms')
    assert e_info.value.args[0] == "Unit prefix 'Brahm' is not available in: Brahms"
        
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
