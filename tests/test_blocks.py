import sys
sys.path.insert(1, '/Users/perseus/Projects/pics/src')
from ParsePPML import *

ppml = r'''
hydro bool = true

height int = none
  = 1
  = 2

  count int = 25 erg/K
    = 23 
    = 24 # something
    = 25 erg/K
    = 55 J # some other text

nums1 int![3] = [4234,34,2]
nums2 float[2:2][2] = [[4234,34],[234,34]] kg
  nums3 int[:2][3] = [[4234,33,34],[234,3,34]]
nums4 int[2:] = [4234,34,234,34]

nums5 int[1:][3] = """
[[4234,34,35],
[234,34,644],
[353,2356,234]]
"""

nums6 str[:] = ["a","bd","c3sa"]
width float! = 23.4 cm
  = 23
  = 23.4 cm
  = 55 m # with comment
  woquotes1 str = noqotes 
  wdquotes2 str = "doub'le # q\"uotes"
    wsquotes3 str = 'sing"le # q\'uotes'
    woquotes4 str = noqotes  # with comment
  wdquotes2.woquotes4 = lalala
text str = """
   tripple qotes # ' " \' \"
block of text
""" # with comment
    # second comment
something
  # comment of else

  # lonely comment
  # second lonely comment
  # all lonely comments will be removed

  # before
  else int = 1  # on
    # after
  foo int = 2
    bar int = 3

count = 24

height.count = 24  # modification
'''

def test_blocks():
    with ParsePPML() as p:
        assert p.parse(ppml)

if __name__ == "__main__":
    print()
    print()
    test_blocks()
