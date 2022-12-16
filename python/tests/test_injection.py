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

def test_injection_nodes():
    data = parse('''
birds
  exotic
    parrots int = 38
    canary int = 23

petshop
  dogs int = 12
  cats int = 45
  (birds.exotic)

jungle (birds.exotic.parrots)

animal.shelter
  dogs int = 34
  cats int = 23
  (birds.exotic.*)
    ''')
    np.testing.assert_equal(data,{
        'birds.exotic.parrots': 38,
        'birds.exotic.canary': 23,
        'petshop.dogs': 12,
        'petshop.cats': 45,
        'petshop.exotic.parrots': 38,
        'petshop.exotic.canary': 23,
        'jungle.parrots': 38,
        'animal.shelter.dogs': 34,
        'animal.shelter.cats': 23,
        'animal.shelter.parrots': 38,
        'animal.shelter.canary': 23,
    })
        
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
