# PPML (Physical Parameter Markup Language)

## Introduction

This markup language was created in order to make initial conditions of physical codes easier and systematic.
Among many interesting features the most important characteristic are:

* hierarchical structure of the settings
* clear description of parameters
* validation of parameter values
* support for physical units
* modularity of DPML files
* parsers for scientific languages
* templating
* parameter overloading

## Implementations

* Fortan
* Python
* C/C++

## Syntax

DPML files share many similar principles with YAML, but contain several important differences.
In this section we discribe its basics.

### Nodes

We call lines with individual parameters and their corresponding settings nodes.
A general format of a single parameter node looks like this:
```
<name> <type><constrain> = <values> <unit> 
  <option>                                 
  <option>
  <option>
  ...
```

Note that node options follow immediatelly after parameter definition and have to be indented.
Types and units have to be defined only first time, when a parameter is defined.
In later sections we will explain various node formats and conversions in details.

#### Names

Node names can consist only lower/upper case letters, numbers, underscores and minus signes.
```
UNIT_L float = 23.3 cm
SongName string = "Yellow submarine"
number-of-votes int = 34
1D bool = true
```
In adition, names cannot start with signs `@`, `&` and `$` because these are reserved for runtime directives.

#### Values

Node values can be either defined or undefined.
Undefined values are, similarily as in other languages, denoted by a special keyword `none`.
```
budget float = none euro
```

One can also add constrains to scalar values in order to enforce their definition.

```
scalar int! = none  # invalid definition, scalar that must be always defined
scalar int  = none  # valid definitionn, scalar that can be undefined
```

#### Hierarchy

Nodes can be ordered in a hierarchical way.
Parent nodes have lower indentation and preceed child nodes.
There has to be always at least one empty line between parent and child nodes.
All child nodes have to have same indentation, higher than the parent node.
Sibling nodes (on the same level of indentation) do not need to be separated by an empty line.
```
family

  parent int = 34 years

    child_1 int = 3 years
    child_2 int = 2 years

    child_3 int = 100 days
```
Notice that node options are directly after node definition, whereas child nodes are separated by an empty line.
Nodes can be used  only as place holders (`family`) that do not have any type or value.

<!---
Above hierarchy is similar to `dictionaries` from Python.
One can also create `list` hierarchies using item notation similar to YAML.
```
family name = "Smith"
  
  - name string = "John"
    age int = 33 years
  
  - name string = "Mary"
    age int = 32 years
```

Note that each list item starts with a hyphen sign and can contain multiple subnodes.

In case a container node do not have any values, one can defined it only using its name.
```
family

  surname string = "Smith"
  
  parents

    - name string = "John"
      age int = 33 years
      
    - name string = "Mary"
      age int = 32 years
  children
  
    - name string = "Laura"
      age int = 3 years
    - name string = "Alex"
      age int = 2 years
    - name string = "Johnatan"
      age int = 100 days
```

Note that sibling nodes/items do not need an empty line betwenn them, but parent/child structures do.
--->

#### Indentation

As a convention we use 2 white spaces for indentation, but this is not a general requirement.
A valid indentation requires 1 or more white spaces.

```
tee string = "Darjeeling"
     "Darjeeling"          # valid indentation for options
     "Pu-Ehr"              # all options need to have consistent indentation
     "Earl Grey"
     *

   weight float = 23.3 g   # valid indentation for a child node
   fresh  bool  = true     # all child nodes need to have consistent indentation
```

#### Comments

Comments in PPML are denoted by a hash tag character.
According to their location and indentation they belong either to previous, next, or no node:
```
# John's comment
# John's comment
parent string = "John"  # John's comment
  # John's comment

  # Comment does not belong to any member of the family
  
  # Michael's comment
  son string = "Michael" # Michael's comment
                         # Michael's comment
    # Michael's comment
  # Julia's comment
  daughter string "Julia" # Julia's comment
    # Julia's comment
    # Julia's comment

hashtag string = "#lovepics"  # hashtags in strings are ignored
``` 

#### Arrays

Nodes can contain vector values, multiple values wrapped into curly brackets and separated by a comma.
Units can be given for each value separately or only once at the end of a definition.
```
<name> <type><constrain> = [<value1>, <value2>, ...] <unit>
<name> <type><constrain> = [<value1> <unit1>, <value2> <unit2>, ...]
```

Most of datatypes can form simple vectors by adding a constrained to the datatype in a following way: 
```
width     float[2]   = [1.3 cm, 2.4 m]       # vector with exactly 2 values
distance  float[1:3] = [1.2e-4, 2.2e-3] au   # vector with 1 to 3 values
guess     int[:3]    = none years            # vector with up to 3 values
icecream  string[1:] = ["lemon", "cherry"]   # vector with 1 or more values
passed    bool[]     = [true, false]         # vector with any number of values
```

It is also possible to create multidimensional arrays.
```
matrix    int[2][3]   = [[2, 3, 4],[5, 8, 5]]   # 2D vector of size 2x3
jacobian  int[1:][:2] = [none,none,none]        # 2D vector of variable size
```

Larger arrays that do not fit into a single line can be also defined using block notation described below.

#### Modifications

Nodes can be modified after they have been defined and they inherit all properties from the definition.
```
size int = 25 cm   # definition
size = 34          # modification
```
Types set by node definitions are immutable and cannot be changed.
```
width float = 23.3 cm            # definition
width float = 22 cm              # valid modification
width = 22 cm                    # valid modification
width float! = 22 cm             # invalid modification
width float[2] = [22 cm, 33 cm]  # invalid modification
width int = 22 cm                # invalid modification
```
Modifications can use different units, however, the final output value of the node will be converted back to original units set in the definition.
```
length float = 1e6 m     # definition
length = 1e5 cm          # valid modification
  # value of length is converted to 1e3 m
```

The same is valid for units in arrays: Modified units will be converted back to units given in the definition.
```
boxsize float = [23.3, 22.5, 56.2] cm     # definition
boxsize = [1.2 m, 22.5, 56.2]             # modification
```

Child nodes can be modified using standard object notation:
```
<parent>.<child> = <values> <unit>
```
A child node mentioned above can be thus modified as:
```
family.parent.child_1 = 1 year
```

### Simple data types

PPML uses similar datatypes as Python, YAML, or JSON.
Four simple datatypes are:

* `bool` - logical boolean value (either integers 0 and 1, or keywords `false` and `true`)
* `int` - integer numbers (precision correspont to 8 bit C integer)
* `float` - floating point numbers (precision correspond to 16 bit C double)
* `str` - string values

A special feature of simple datatypes is that they can have predefined options.
Such parameter definition are especially usefull in case of preprocessor flags and runtime parameter.
Individual optons are listed directly below (without empty line) parameter definition.
It is a good habit to add description of parameters in the comment.
```
geometry int = 0             # definition
  0  # 1-dimensional grid
  1  # 2-dimensional grid
  2  # 3-dimensional grid

geometry = 2                 # valid modification
geometry = 3                 # invalid modification
```
If options are set in definition, no other modifications are allowed besides the options.
It is possible to explicitely allow other values by adding a wildcard option to the end using asterix `*` symbol.
```
scale float = 12 cm          # definition
  12 cm   # small sample
  25 cm   # large sample
  35 cm   # extra large sample
  *       # custom sample

scale = 25 cm                # valid modification
scale = 12.3 cm              # also valid modification
```

The only type that does not explicitly support options is `boolean`.
In case of booleans implicit options are always keywords `true` or `false` (or integers 1 and 0).
```
eat bool = true
snack bool = 0
```

Strings that contain only one word (and no empty spaces) can be given without qotemarks.
Phrases and sentences need to be wrapped into either single, or double qotemarks.
As it is usual in other languages, the same qotemarks used within the string have to be escaped.
```
description string = "PPML stands for \"Physical Property Markup Language\""
restaurant string = "Mandy's Railway Diner"
color string = blue
  red
  green
  blue
```

Booleans and strings by design do not support units.

### Block data types

Long data types are used to describe values that do not fit into a single line.
Into this cathegory belong following:

* `text`- large block of text
* `table` - tabular data
* `block arrays` - large multidimensional arrays

It is also possible to assign large texts to parameters using triple quote notation.
Text starts directly at the following line without indentation.
End of the text is marked by final triple qotes on a new line.
These also do not need to be indented.
```
product string = pen           # definition

  price float = 33.90 euro
  description text = """       # tripple qotes as a value
Our pens are built from best and eco-friendly materials.

We guarantee that you will be satisfied with quality of our products.
"""

product.description = """      # modification
We appologize for poor quality of our products and customers can 
claim their refund at our sails department.
"""		    
```

Tables are special text blocs that contain ordered numerical or string data.
Columns have to be separated by empty spaces.
Similarily as text, also table values are contained within tripple qotes.
In addition, tables must include in header options with column names, types and optionally units.
There should be an empty line between header and table values.
```
belts table = """ 
marking string
size float
waist float cm

S  2 81.0
M  3 91.0
L  4 102.0
"""
```

Table definition can include only table header.
Inline modifications to tables do not necessarily need to include a header.
```
belts table = """    # definition
marking string
size float
waist float cm
"""

# Department with extra sizes
belts = """          # modification
XS 1 71.0
S  2 81.0
M  3 91.0
L  4 102.0
XL 5 112.0
"""
```
Tables defined in an external file should always contain a header.
For clarification see later chapters about runtime directives.

Another data type that uses block strucutre are block arrays.
In principle, block arrays are the same as arrays of simple datatypes.
They are desinged to contain large arrays of data that do not fit into a single line.
Syntax for block arrays is similar to text and tables.
```
jacobian int[6][6] = """
[[34,423,540,493,248,2],
[43,24,340,349,3940,4],
[23,34,3490,203,2304,24],
[41,58,2349,2394,234,12],
[934,2349,2348,2034,249,34],
[034,57,1930,234,2340,34]]  
"""
```
Units of array values must be defined within the block.
```
sizes float[3][3] = """
[[23.4, 6.45, 6.3],
[35.6, 73.4, 327.4],
[5.3, 81.76, 453.4]] cm
"""
```

### Runtime directives

Runtime directives are used to improve calarity of PPML files and to specify node dependencies.
Each directive starts with a different symbol:

* `&` - include nodes/blocks from an external file
* `$` - define/include a node structure
* `@` - add condition to single or multiple nodes

One can include content of nother PPML file into current using `&<file>` directive.
The content will be included at the place (and with an indent) where directive is called.
In the case below, the content of `spherical.ppml` will be included under the parent node `point`.
```
# Included file: spherical.ppml

theta float = 23.3
rho float = 334.3
radius float = 234

# Current file: points.ppml

point

  &./spherical.ppml     # Content of sperical.ppml will be included here
```

If the directive is used in the value part of a node definition, the content is imported as a block data.
```
# Included table: ./output_times.ppml

output bool
time float s

1 2.34
0 34.23
0 144.34
1 234.34

# Current file: parameters.ppml

ouput_times table = &./output_times.pplm
```

In a similar way one can define node or block structure in a variable using `$<name>` directive.
Later this structure can be imported into already existing node.
Note that variable definition cannot be indented, but all members of the variables need to have some level of indentation.
```
# Define a node structure

$lunch           # definition cannot be indented
                 # empty line is optionable
  appetizer string = "antipasti"
  soup string = "gazpacho"
  main_course string = "carbonara"
  dessert string = "tiramisu"

# Use the node structure in another structure

booking

  room int = 1 
  beds int = 2
  $lunch         # insertion
```
The above example will append child nodes of the `$lunch` to the booking node.
Below is an example of a block structure.
```
$description = """          # definition
This description is stored into a variable called $description
and included into another node.
"""

about_us text = $description   # insertion
about_uk text = $description   # multiple insertions are also possible
```

Conditional directive (starting with `@` sign) is applied only for the next node (with the same indent level), or on all immediate child nodes (with higher indents). One can use following standart logical operators: `==`, `>`, `>=`, `<`, `<=`, `!=`. `&&`, `||`.

```
marriage string = no

@ marriage == no          # condition flag on the same indent affects only next node
reason string = "I thought we were just friends" 

@ marriage == yes || marriage != no     # condition for multiple nodes
  	      	     	      	 	# empty line is optional
  reason string = "I love you!"
  salary float  = 4e3 euro    
  house bool    = true        
```
