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

"""
def test_variable_nodes():
    data = parse('''
$birds
  parrots int = 38
  canary int = 23

petshop
  dogs int = 12
  cats int = 45
  $birds

shelter
  dogs int = 34
  cats int = 23
  $birds
    ''')
    np.testing.assert_equal(data,{
        'petshop.dogs': 12,
        'petshop.cats': 45,
        'petshop.parrots': 38,
        'petshop.canary': 23,
        'shelter.dogs': 34,
        'shelter.cats': 23,
        'shelter.parrots': 38,
        'shelter.canary': 23,
    })
"""
        
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
