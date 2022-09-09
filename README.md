# PICS (Physical Initial ConditionS)

## Introduction

This markup language was created in order to make initial conditions of physical codes easier and systematic.
Among many interesting features the most important characteristic are:

* hierarchical structure of the settings
* clear description of parameters
* validation of parameter values
* support for physical units
* modularity of PICS files
* parsers for scientific languages
* templating
* parameter overloading

## Implementations

* Fortan
* Python
* C/C++

## Syntax

### Basics

PICS files share many similar principles with YAML, but contain several important differences.
In this section we discribe its basics.

#### General format

We call lines with individual parameters 'nodes'.
A general format of a single node looks like this:
```
@ <conditions>
<name> <type> = <value> <unit>
  <setting>
  <setting>
  <setting>
  ...
```
Note that node `<setting>`-s follow immediatelly after its definition and are indented.
`<type>` and `<unit>` do need to be defined only first time, when the parameter is defined.
All other occurences inherit the same `<type>`.
`<unit>`-s of subsequent occurences can be different.
In later sections we will explain various node formats in details.

#### Hierarchy

Nodes can be ordered in a hierarchy.
Parent nodes have lower indentation and preceed child nodes.
There has to be always at least one empty line between parent and child nodes.
All child nodes have to have same indentation, higher than the parent node.
Sibling nodes (on the same level of indentation) do not need to be separated by an empty line.
```
parent int = 33 year

  child_1 int = 1 year
  child_2 int = 2 year
```
Notice that node settings are directly after node definition, whereas child nodes are separated by an empty line.

#### Indentation

As a convention we use 2 white spaces for indentation, but this is not a general requirement.
A valid indentation requires 1 or more white spaces.

### Basic datatypes

```
scalar int!     = 3        # integer that must be defined
scalar int      = none     # integer that can be undefined
array  int[2]   = 1, 2     # array with exactly 2 values
array  int[1:3] = 1, 2     # array with 1 to 3 values
array  int[:3]  = none     # array with up to 3 values
array  int[1:]  = 1, 2, 3  # array of integers with 1 or more values
array  int[:]   = none     # array with any number of values
```

```
dimensions  int = 3        # integers with options
  # no free line allowed here
  1 # linear
  2 # cylindrical
  3 # spherical
```

```
# nodes on the same indent level do not need to be separated by an empty line
number    float  = 1.3e-3           # float number with undefined units
constant  float  = 3.4e23 cm        # number in units of centimeters
energy    float! = 3.4e23 g*cm2/s2  # number in complex units of energy has to be set
energy    float  = none J           # energy in Joules that can be none
```

```
power float[2] = 2.3 erg/s, 3.4 W   # units with different notation
  # no free line allowed here
  1.2 erg/s     # low power in cgs
  3.4 W         # average power in SI Watts
  5.5 J/s       # high power in SI complex units
```

```
logical bool    = true         # logical true/false value
logical bool[3] = false, 1, 0  # logical array with integer notation 
```

```
box dict               # dictionary with four components
  # no free line allowed here
  x float = 2.3e2 cm   # size in x direction
  y float = 4.8e2 cm   # size in y direction
  z float = 2.3e2 cm   # size in z direction
  boundary int = 1     # boundary conditions with fixed options
    0 # rigid
    1 # free
    2 # overflow
```

```
variable int = 4 # comment on the variable

# comment preceeding the variable has the same indent
variable int = 3

marriage string = yes  # one word strings do not need quotation marks
  # comment after the variable must be indented
  no   # rejective answer requires
       # more comments also on the line below
  yes  # affirmative

  @ vote == no          # condition flag on the same indent affects only following node
  reason string! = "I thought we were just friends"  # one has to give a reason
    # For strings with multiple words one needs to use qotation marks

  @ vote == yes         # there can be even a free line in between
  
  reason string  = none # reason does not heed to be defined

  @ vote == yes | vote != no     # condition for multiple nodes
    # can be followed by an empty line, but the members must be indented
    
    salary float!  = 4e3 euro    # must be set
    house bool!    = true        # must be set
```

```
marriage.reason = "love"  # shorthand for setting the variables

output table[:4]   # table can have up to four rows
  # header specification needs to be set directly after a table declaration
  step int
  time float s
  energy float J
  description string

# table values do not need to be indented and can have a free line in front
0 234.34e3 22.3e-3 "small"    # space separated values
0 34.34e3  23.3e-3 "big"
0 234.4e3  22.3e-3 "large"
0 334.34e3 2.3e-3  "extreme"
# table ends with an empty line
```