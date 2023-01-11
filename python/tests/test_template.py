import sys, os
import pytest
import numpy as np

sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'src'))
from DPML import *

def test_template():
    code = """
    name str = 'Tina'
    body
      weight float = 62.3 kg
      height float = 177 cm
    age int = 30 a
    gender str = 'woman'
      = 'woman'
      = 'man'
    """
    with DPML(code) as p:
        p.initialize()
        result = p.template("""
Name:   {{?name}:s}
Weight: {{?body.weight}:.3e}
Height: {{?body.height}}
Age:    {{?age}}
Gender: {{?gender}}
        """)
        print(result)
        assert result == """
Name:   Tina
Weight: 6.230e+01
Height: 177.0
Age:    30
Gender: woman
        """
        
if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
