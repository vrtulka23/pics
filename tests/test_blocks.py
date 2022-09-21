import sys
sys.path.insert(1, '/Users/perseus/Projects/pics/src')
from ParsePPML import *

ppml = r'''
hydro bool = true
count int = 23 erg/K
nums1 int![3] = [4234.3,34,2]
nums2 float[2:2][2] = [[4234,34],[234,34]]
nums3 int[:2][2] = [[4234,34],[234,34]]
nums4 int[2:] = [4234,34,234,34]
nums5 str[:] = ["a","bd","c3sa"]
width float! = 23.4 cm
  woquotes1 str = noqotes 
  wdquotes2 str = "doub'le # q\"uotes"
  wsquotes3 str = 'sing"le # q\'uotes'
  woquotes4 str = noqotes  # with comment
text str = """
   tripple qotes # ' " \' \"
block
""" # with comment
someting
'''

def test_blocks():
    with ParsePPML() as p:
        assert p.parse(ppml)

if __name__ == "__main__":
    test_blocks()
