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

def test_invalid_start():
    with pytest.raises(Exception) as e_info:
        parse('''
        @end
        ''')
    assert e_info.value.args[0] == "Invalid condition:"
    assert e_info.value.args[1] == "@end"
    with pytest.raises(Exception) as e_info:
        parse('''
        @else
           car str = 'BMW'
        ''')
    assert e_info.value.args[0] == "Invalid condition:"
    assert e_info.value.args[1] == "@else"
    with pytest.raises(Exception) as e_info:
        parse('''
        @case true
          @end
        ''')
    assert e_info.value.args[0] == "Invalid condition:"
    assert e_info.value.args[1] == "@case.@end"
    
def test_nested_condition():
    data = parse('''
    @case false
      flower str = 'rose'
    @else
      flower str = 'dandelion'
      @case false
        color str = 'red'
      @case false
        color str = 'blue'
      @else
        @case true
          leaves int = 234
        color str = 'yellow'
    tree str = 'maple'
    ''')
    np.testing.assert_equal(data,{
        'flower': 'dandelion',
        'leaves': 234,
        'color': 'yellow',
        'tree': 'maple',
    })
    
def test_modifications():
    data = parse('''
    star str = 'Sun'

    @case false
      star = 'Sirius'
      nebula str = 'Orion'
    @else
      star = 'Wega'
      nebula str = 'Crab'

    nebula = 'Eagle'
    ''')
    np.testing.assert_equal(data,{
        'star': 'Wega',
        'nebula': 'Eagle',
    })
    
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

def test_expression():
    data = parse('''
trafic

  # definitions
  limit float = 75 km/s 
  urban bool = true

  # first case with inline conditions
  @case {?trafic.limit} <= 50 km/s || {?trafic.urban}

    road str = 'town'

  # second case with a block condition
  @case """
  ( {?trafic.limit} <= 100 km/s && {?trafic.limit} > 50 km/s )
  && !{?trafic.urban}
  """

    road str = 'country'

  # if none of the cases apply
  @else

    road str = 'motorway'

  @end

  cars int = 12  # outside of case
    ''')
    np.testing.assert_equal(data,{
        'trafic.limit': 75,
        'trafic.urban': True,
        'trafic.road': 'town',
        'trafic.cars': 12,
    })
  
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
