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

def test_case():
    data = parse('''
    climate
      @case true                  # true condition
        warming bool = true       # nodes belonging to a case have higher indent
          increase float = 2 Cel  # subnodes also belong to the above case

      temperature float = 10.2 Cel   # case ends if indent of a new node is lower

    plant
      @case true                # first condition is true
        leaves int = 1302       
      @case false
        leaves int = 12304
      @end                      # case ends when explicitely terminated

    plant.@case false           # using compact node names
        flower str = 'green'
    plant.@case true            # second condition is true
        flower str = 'yellow'   
    plant.@else                 # else is not triggered
        flower str = 'red'

    animal
      @case false
        cat str = 'lion'
      @case false
        cat str = 'tiger'
      @else                     # return else, because none of the cases were true
        cat str = 'gepard'        
    ''')
    np.testing.assert_equal(data,{
        'climate.warming': True,
        'climate.warming.increase': 2,
        'climate.temperature': 10.2,
        'plant.leaves': 1302,
        'plant.flower': 'yellow',
        'animal.cat': 'gepard',
    })

"""
def test_expression():
    data = parse('''
trafic

  # definitions
  limit float = 75 km/s 
  urban bool = true

  # first case with inline conditions
  @case {?limit} <= 50 km/s || {?urban}

    road str = 'town'
    stuff int = 1
      substuff float = 1.3

  # second case with a block condition
  @case \"\"\"
  ( {?limit} <= 100 km/s && {?limit} > 50 km/s )
  && ! {?urban}
  \"\"\"

    road str = 'country'

  # if none of the cases apply
  @else

    road str = 'motorway'

  @end

  cars int = 12  # outside of case
    ''')
    np.testing.assert_equal(data,{
        'limit': 75,
        'road': 'country',
        'cars': 12,
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
