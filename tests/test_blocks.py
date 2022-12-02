import sys
sys.path.insert(1, '/Users/perseus/Projects/pics/src')
from ParsePPML import *
import pytest
import numpy as np

def parse(code):
    with ParsePPML(code) as p:
        p.initialize()
        p.finalize()
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
age int = 20
weight float = 63.3
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
length float! = none
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
lengths float[2:][2] = [[4234,34],[234,34]]
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
    
def test_blocks():
    data = parse('''
matrix int[1:][3] = """
[[4234,34,35],
   [234,34,644],
[353,2356,234]]
  """  # endqotes can be indented
outputs table = """
time float s
snapshot int
intensity float W/m2

0.234 0 2.34
1.355 1 9.4
2.535 2 3.4
3.255 3 2.3
4.455 4 23.4
"""
text str = """
   tripple qotes # ' " \' \"
block of text
""" 
    ''')
    np.testing.assert_equal(data,{
        'matrix': np.array([[4234,   34,   35],[ 234,   34,  644],[ 353, 2356,  234]]),
        'outputs.time': np.array([0.234, 1.355, 2.535, 3.255, 4.455]),
        'outputs.snapshot': np.array([0, 1, 2, 3, 4]),
        'outputs.intensity': np.array([ 2.34,  9.4 ,  3.4 ,  2.3 , 23.4 ]),
        'text': '   tripple qotes # \' " \' "\nblock of text'
    })

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
    
def test_imports():
    data = parse('''
{tests/block_nodes.txt}                        # base import
box
  {tests/block_nodes.txt}                      # import into a group node
basket.bag {tests/block_nodes.txt}             # import into a namespace
blocks                                         # block imports into a group node
  matrix int[3][4] = {tests/block_matrix.txt}  # import a dimensional array
  table table = {tests/block_table.txt}        # import a table
  text str = {tests/block_text.txt}            # import large text
    ''')
    np.testing.assert_equal(data,{
        'fruits': 0,
        'vegies': 1,
        'vegies.potato': 200.0,
        'box.fruits': 0,
        'box.vegies': 1,
        'box.vegies.potato': 200.0,
        'basket.bag.fruits': 0,
        'basket.bag.vegies': 1,
        'basket.bag.vegies.potato': 200.0,
        'blocks.matrix': np.array([[4234,   34,   35,   34],[ 234,   34,  644,   43],[ 353, 2356,  234,    3]]),
        'blocks.table.x': np.array([0.234, 1.355, 2.535, 3.255, 4.455]),
        'blocks.table.y': np.array([0.234 , 1.43  , 2.423 , 3.2355, 4.2356]),
        'blocks.text': 'This is a block text\nwith multiple lines\nthat will be loaded to a\nstring node.\n'
    })

def test_mods():
    data = parse('''
size float = 70 cm    # definition
size float = 80 cm    # modifications of value
size = 90 cm          # omitting datatype
size = 100            # omitting units
size = 1 m            # using different prefix

energy float = 1.23 J # definition
energy = 2.2 erg      # switching from SI to cgs
energy = 2.2 g.cm2/s2 # using unit expressions

angle float = 1.57079633 rad    # using numbers 
angle = 30 deg                  # definition
    ''')
    np.testing.assert_equal(data,{
        'size':   100,
        'energy': 2.2e-7,
        'angle':  0.5235987,
    })  
        
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
