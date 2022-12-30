import sys, os
import pytest
import numpy as np

sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'src'))
from ParseDPML import *

def parse(code):
    with ParseDPML(code) as p:
        p.initialize()
        p.display()
        return p.data()

def test_import_nodes():
    data = parse('''
{tests/blocks/nodes.dpml}                        # base import
box
  {tests/blocks/nodes.dpml}                      # import into a group node
basket.bag {tests/blocks/nodes.dpml}             # import into a namespace
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
    })

def test_query_remote():
    data = parse('''
bag {tests/blocks/nodes.dpml?*}                # import all
bowl 
  {tests/blocks/nodes.dpml?fruits}             # selecting a specific node
  {tests/blocks/nodes.dpml?vegies.potato}      # selecting a specific subnode
plate {tests/blocks/nodes.dpml?vegies.*}       # selecting all subnodes
    ''')
    np.testing.assert_equal(data,{
        'bag.fruits': 0,
        'bag.vegies': 1,
        'bag.vegies.potato': 200.0,
        'bowl.fruits': 0,
        'bowl.potato': 200.0,
        'plate.potato': 200.0,
    })
    
def test_query_local():
    data = parse('''
icecream 
  waffle str = 'standard'
  scoops
    strawberry int = 1 #some comment
    chocolate int = 2

bowl
  {?icecream.scoops.*}      # select subnodes from current file
plate {?icecream.waffle}    # select specific node from current file
    ''')
    np.testing.assert_equal(data,{
        'icecream.waffle': 'standard',
        'icecream.scoops.strawberry': 1,
        'icecream.scoops.chocolate': 2,
        'bowl.strawberry': 1,
        'bowl.chocolate': 2,
        'plate.waffle': 'standard',
    })

def test_value_local():
    data = parse('''
size1 float = 34 cm
size2 float = {?size1} m  # definition using import
size1 = {?size2}          # modifying by import
    ''')
    print(data)
    np.testing.assert_equal(data,{
        'size1': 3400,  # 100 cm = 1 m 
        'size2': 34,    # m
    })

def test_value_remote():
    data = parse('''
energy float = 34 erg
energy float = {tests/blocks/query.dpml?energy}  # import with a type
energy = {tests/blocks/query.dpml?energy} eV     # import value only but set a different unit
energy = {tests/blocks/query.dpml?energy}        # import both value and unit
    ''')
    np.testing.assert_equal(data,{
        'energy': 13.0e7           # converted to original units
    })
    with pytest.raises(Exception) as e_info:
        parse('energy float = {tests/blocks/query.dpml?*}')
    assert e_info.value.args[0] == "Query returned multiple nodes for a value import: *"
    
def test_import_matrix():
    data = parse('''
blocks                          # block imports into a group node
  matrix1 int[3][4] = {tests/blocks/matrix.txt}          # import a text file
  matrix2 int[3][4] = {tests/blocks/query.dpml?matrix}   # import value of a specific node
    ''')
    np.testing.assert_equal(data,{
        'blocks.matrix1': np.array([[4234,   34,   35,   34],[ 234,   34,  644,   43],[ 353, 2356,  234,    3]]),
        'blocks.matrix2': np.array([[4234,   34,   35,   34],[ 234,   34,  644,   43],[ 353, 2356,  234,    3]]),
    })
    
def test_import_table():
    data = parse('''
blocks                             # block imports into a group node
  table1 table = {tests/blocks/table.txt}         # import a text file
  table2 table = {tests/blocks/query.dpml?table}  # import value of a specific node
    ''')
    np.testing.assert_equal(data,{
        'blocks.table1.x': np.array([0.234, 1.355, 2.535, 3.255, 4.455]),
        'blocks.table1.y': np.array([0.234 , 1.43  , 2.423 , 3.2355, 4.2356]),
        'blocks.table2.x': np.array([0.234, 1.355, 2.535, 3.255, 4.455]),
        'blocks.table2.y': np.array([0.234 , 1.43  , 2.423 , 3.2355, 4.2356]),
    })
    
def test_import_text():
    data = parse('''
blocks                               # block imports into a group node
  text1 str = {tests/blocks/text.txt}            # import a text file
  text2 str = {tests/blocks/query.dpml?text}     # import value of a specific node
    ''')
    np.testing.assert_equal(data,{
        'blocks.text1': 'This is a block text\nwith multiple lines\nthat will be loaded to a\nstring node.\n',
        'blocks.text2': 'This is a block text\nwith multiple lines\nthat will be loaded to a\nstring node.',
    })

            
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
