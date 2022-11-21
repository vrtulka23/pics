import sys
sys.path.insert(1, '/Users/perseus/Projects/pics/src')
from ParsePPML import *
import pytest
import numpy as np

ppml = r'''
hydro bool = true

height int = none
  = 1
  = 2

  count int = 25 erg/K
    = 23 
    = 24 # something
    = 25 erg/K
    = 55 J # some other text

height.count = 24  # modification
height.count = 55 # last mod

nums1 int![3] = [4234,34,2]
nums2 float[2:2][2] = [[4234,34],[234,34]] kg
  nums3 int[:2][3] = [[4234,33,34],[234,3,34]]
nums4 int[2:] = [4234,34,234,34]

blocks

  matrix int[1:][3] = """
[[4234,34,35],
[234,34,644],
[353,2356,234]]
"""
  matrix2 int[1:][3:] = {tests/block_matrix.txt}

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

  outputs2 table = {tests/block_table.txt}

  text str = """
   tripple qotes # ' " \' \"
block of text
""" # with comment
    # second comment

  text2 str = {tests/block_text.txt}

  {tests/block_nodes.txt} # import nodes to blocks

blocks2.{tests/block_nodes.txt}  # import nodes to blocks2

nums6 str[:] = ["a","bd","c3sa"]
width float! = 23.4 cm
  = 23
  = 23.4 cm
  = 55 m # with comment
  woquotes1 str = noqotes 
  wdquotes2 str = "doub'le # q\"uotes"
    wsquotes3 str = 'sing"le # q\'uotes'
    woquotes4 str = noqotes  # with comment
  wdquotes2.woquotes4 = lalala
something
  # comment of else

  # lonely comment
  # second lonely comment
  # all lonely comments will be removed

  # before
  else int = 1  # on
    # after
  foo int = 2
    bar int = 3
'''

def parse(code):
    with ParsePPML(code) as p:
        p.initialize()
        p.finalize()
        p.display()
        return p.data()

def test_name():
    data = parse('''
complicated.node23.NAME int = 1
    ''')
    np.testing.assert_equal(data,{
        'complicated.node23.NAME': 1,
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
    data = parse('counts int! = 3')
    np.testing.assert_equal(data,{
        'counts': 3
    })
    with pytest.raises(Exception) as e_info:
        parse('counts int! = none')
    assert e_info.value.args[0] == "Value of node 'counts' must be defined"

def test_quotes():
    data = parse('''
name str = "Johannes Brahms"
counts int[3] = "[0, 1, 2]"
answers bool[2] = "[true, false]"
names str[2] = '["Jolana", "Anastasia"]'
    ''')
    np.testing.assert_equal(data,{
        'name': 'Johannes Brahms',
        'counts': np.array([0, 1, 2]),
        'answers': np.array([ True, False]),
        'names': np.array(['Jolana', 'Anastasia'], dtype='<U9')
    })
    with pytest.raises(Exception) as e_info:
        parse('name str = Johannes Brahms')
    assert e_info.value.args[0] == "Invalid units: Brahms"
    
def test_blocks():
    data = parse('''
matrix int[1:][3] = """
[[4234,34,35],
   [234,34,644],
[353,2356,234]]
  """  # here we test also various indentations
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
  {tests/block_nodes.txt}                      # import into a node group
basket.bag {tests/block_nodes.txt}             # import into a namespace
blocks
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
    
if __name__ == "__main__":
    print()
    print()
    test_name()
    test_types()
    test_dimensions()
    test_defined()
    test_quotes()
    test_blocks()
    test_hierarchy()
    test_imports()
