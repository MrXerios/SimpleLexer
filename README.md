# SimpleLexer
A small general purpose lexer, designed to be inherited. The python lexer is also available in this repository. This lexer is heavily inspired by Pygments, though it is a simpler version I wanted to code myself.

The file ``lexer/unistring.py`` is directly sources from the Pygments project (https://github.com/pygments/pygments/tree/master/pygments)

## TODO

- Improve soft-keyword processing (matche..case),
- Change float number recognition to find ``.05`` and ``3e8`` properly,
- Add type hints recognition (*-*)
