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
    
def test_inline_matrix():
    data = parse('''
matrix int[1:][3] = """
[[4234,34,35],
   [234,34,644],
[353,2356,234]]
"""
    ''')
    np.testing.assert_equal(data,{
        'matrix': np.array([[4234,   34,   35],[ 234,   34,  644],[ 353, 2356,  234]]),
    })

def test_inline_table():
    data = parse('''
outputs table = """
time float s
snapshot int
intensity float W/m2

0.234 0 2.34
1.355 1 9.4
2.535 2 3.4
3.255 3 2.3
4.455 4 23.4
  """  # endqotes can be indented
    ''')
    np.testing.assert_equal(data,{
        'outputs.time': np.array([0.234, 1.355, 2.535, 3.255, 4.455]),
        'outputs.snapshot': np.array([0, 1, 2, 3, 4]),
        'outputs.intensity': np.array([ 2.34,  9.4 ,  3.4 ,  2.3 , 23.4 ]),
    })

    
def test_inline_text():
    data = parse('''
text str = """
   tripple qotes # ' " \' \"
block of text
""" 
    ''')
    np.testing.assert_equal(data,{
        'text': '   tripple qotes # \' " \' "\nblock of text'
    })
        
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
