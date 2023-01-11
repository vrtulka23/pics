DPML - Dimensional Parameter Made Legible
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Welcome to DPML documentation. Right from beginning, we need to add a disclaimer, that this is not a Markup Language, but a parameter serialization language. We wanted to preserve naming convention of other serialization languages like YAML or TOML and thus set this language as an alternative to them. 

DPML is specifically designed as a parameter parser for massive parallel codes used in physics, mathematics and engeneering that are mostly written in C/C++ and Fortran. Such codes require parameter input of multiple quantities and compilation flags with precisely defined variable types and physical units. In large projects this can get quickly messy and confusing. Especially when code requires to set parameters using several different, code specific (C/C++ pre-processor constants, Bash/Shell environmental variables, CSV and data tables, or Json, YAML, TOML and similar), notations and adjustable units units.

The most notable features of this language are:

- Hierarchical parameter structure

  .. code-block::

     human
       head
         nose int = 1
     human.head.eye int = 2
       
- Explicit unit definitions of parameters

  .. code-block::

     weight float = 56 kg
     velocity float = 1.78 km/s

- Sequential modification of parameters

  .. code-block::

     dimensions int = 1
     dimensions = 2
     dimensions = 3

- Automatic unit conversion between parameter modifications and definition

  .. code-block::

     energy float = 3 J
     energy = 4 eV

- Explicit definition of parameter options and their validation

  .. code-block::

     geometry int = 1
       = 1  # line
       = 2  # plane
       = 3  # volume

- Inclusion of parameter values and node from local and external sources

  .. code-block::

     fruits int = 2

     basket
       pear int = {?fruits}
       {./vegetables.dpml?carrots}       

- Conditional serialization of parameters

  .. code-block::

     source bool = true
     
     @case {?ray_tracing}
        intensity float = 23 W/m2
     @else
        intensity float = none

- Modularization of parameter files (serialization of multiple DPML files together)
- Definition of parameter data types (integer, float, string, double)
- Native serialization in Python, C/C++ (TODO) and Fortran (TODO)
- Template parsing (e.g. producing of pre-processor flag parameter files)
- Support of tabular data intput (e.g. CSV format or similar)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
