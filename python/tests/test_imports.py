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

def test_import_nodes():
    data = parse('''
{tests/blocks/nodes.txt}                        # base import
box
  {tests/blocks/nodes.txt}                      # import into a group node
basket.bag {tests/blocks/nodes.txt}             # import into a namespace
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

def test_import_matrix():
    data = parse('''
blocks                                         # block imports into a group node
  matrix int[3][4] = {tests/blocks/matrix.txt}  # import a dimensional array
    ''')
    np.testing.assert_equal(data,{
        'blocks.matrix': np.array([[4234,   34,   35,   34],[ 234,   34,  644,   43],[ 353, 2356,  234,    3]]),
    })
    
def test_import_table():
    data = parse('''
blocks                                         # block imports into a group node
  table table = {tests/blocks/table.txt}        # import a table
    ''')
    np.testing.assert_equal(data,{
        'blocks.table.x': np.array([0.234, 1.355, 2.535, 3.255, 4.455]),
        'blocks.table.y': np.array([0.234 , 1.43  , 2.423 , 3.2355, 4.2356]),
    })
    
def test_import_text():
    data = parse('''
blocks                                         # block imports into a group node
  text str = {tests/blocks/text.txt}            # import large text
    ''')
    np.testing.assert_equal(data,{
        'blocks.text': 'This is a block text\nwith multiple lines\nthat will be loaded to a\nstring node.\n'
    })

            
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
