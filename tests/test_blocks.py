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

height.count = 24  # modification
height.count = 55 # last mod

nums1 int![3] = [4234,34,2]
nums2 float[2:2][2] = [[4234,34],[234,34]] kg
  nums3 int[:2][3] = [[4234,33,34],[234,3,34]]
nums4 int[2:] = [4234,34,234,34]

blocks

  matrix int[1:][3] = """
[[4234,34,35],
[234,34,644],
[353,2356,234]]
"""
  matrix2 int[1:][3:] = {tests/block_matrix.txt}

  outputs table = """
time float s
snapshot int
intensity float W/m2

0.234 0 2.34
1.355 1 9.4
2.535 2 3.4
3.255 3 2.3
4.455 4 23.4
  """

  outputs2 table = {tests/block_table.txt}

  text str = """
   tripple qotes # ' " \' \"
block of text
""" # with comment
    # second comment

  text2 str = {tests/block_text.txt}

  {tests/block_nodes.txt} # import nodes to blocks

blocks2.{tests/block_nodes.txt}  # import nodes to blocks2

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
'''

def test_blocks():
    with ParsePPML(ppml) as p:
        p.initialize()
        p.finalize()
        p.display()
    assert True

if __name__ == "__main__":
    print()
    print()
    test_blocks()
