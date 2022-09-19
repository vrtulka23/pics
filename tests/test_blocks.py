import sys
sys.path.insert(1, '/Users/perseus/Projects/pics/src')
from ParsePPML import *

ppml = '''
hydro bool = true
count int = 23
nums int![3] = [4234]
nums int[2:2] = [[4234,34],[234,34]]
nums int[:2] = [[4234,34],[234,34]]
nums int[2:] = [[4234,34],[234,34]]
nums int[:] = [[4234,34],[234,34]]
width float! = 23.4 cm
  woquotes str = noqotes  # with comment
  wdquotes str = "double quotes"
  wsquotes str = 'single quotes'
text str = """
   tripple qotes
block
""" # with comment
someting
'''

def test_blocks():
    with ParsePPML() as p:
        assert p.parse(ppml)

if __name__ == "__main__":
    test_blocks()
