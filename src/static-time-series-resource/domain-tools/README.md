# Domain tools

Miscellaneous shared domain specific code for the simulation platform.

## Contents

Contains the domain\_tools Python package which can have subpackages related to various domain topics. Currently contains the following:

- resource: Code related to simulation resources.
    - resource\_state\_source: Code for representing a resource state and for reading it from a csv file.

## Including to other python project

You can simply copy the domain_tools folder to your project (not recommended) or include this repository as a git submodule of your project. For more detailed instructions you can use the steps described in the [simulation-tools](https://github.com/simcesplatform/simulation-tools)
repository by just replacing simulation-tools with this repository.

## Tests

Execute unit tests:

```python
python -m unittest
```
