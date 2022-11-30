import sys
sys.path.insert(1, '/Users/perseus/Projects/pics/src')
from PUML_Parse import *
import pytest
import numpy as np

def test_units():
    PUML_Parse('10*2.cm2.s-1/(W.g)')

if __name__ == "__main__":
    # Specify wich test to run
    test = sys.argv[1] if len(sys.argv)>1 else True

    # Loop through all tests
    for fn in dir(sys.modules[__name__]):
        if fn[:5]=='test_' and (test is True or test==fn[5:]):
            print(f"\nTesting: {fn}\n")
            locals()[fn]()
