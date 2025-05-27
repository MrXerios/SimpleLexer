import re
import keyword

from lexer.lexer_base import Lexer, bygroups, from_list, include, default, combination
from lexer.tokens import _token_type
import lexer.unistring as uni

operator_list = [re.escape(p) for p in r"+ - * / % * ** / // @ & | ^ ~ >> << == = := += -= *= /= %= *= **= @= &= |= ^= >>= <<= >= <= != < >".split(" ")]


list_builtins = dir(__builtins__)


# Define root of tokens
Syntax = _token_type()

# Aliases
Whitespace = Syntax.Whitespace
String = Syntax.String
SString = String.Simple
FString = String.Formatted
Comment = Syntax.Comment
Keyword = Syntax.Keyword
Name = Syntax.Name
Operator = Syntax.Operator
Number = Syntax.Number
Punctuation = Syntax.Punctuation

class PythonLexer(Lexer):

    # Regex for possible syntax for an identifier using unicode
    uni_name = f"[{uni.xid_start}][{uni.xid_continue}]*"

    states = {
        'root': [
            # for speed: immediate match on empty lines
            (r'\Z', Whitespace),

            (r'\A#!.+$', Comment.Hashbang),
            (r'#[ \t]*(?i:todo|2do|fixme).*$', Comment.Todo),
            (r'#.*$', Comment), # Simple comment
            (r'^[ \t]*##.*$', Comment.Cell), # Comment cell
            (fr'(def)([ \t]+)({uni_name})', bygroups(Keyword, Whitespace, Name.Function)),
            (fr'(class)([ \t]+)({uni_name})', bygroups(Keyword, Whitespace, Name.Class)),
            (fr'@{uni_name}', Name.Decorator),
            include("expression"),
        ],
        "expression": [
            # Parenthesis
            (r'[\(\{\[]', Syntax.Open),
            (r'[\)\}\]]', Syntax.Close),

            # Non-formatted Strings
            # Multiline strings
            (r"([uUrRbB]{,2})(?=''')", String.Literal, "string-single-multiline"),
            (r'([uUrRbB]{,2})(?=""")', String.Literal, "string-double-multiline"),

            # One line strings
            (r"([uUrRbB]{,2})(?=')", String.Literal, "string-single-oneline"),
            (r'([uUrRbB]{,2})(?=")', String.Literal, "string-double-oneline"),

            # Formatted strings (and templates from python 3.14)
            # Multiline fstrings
            (r"([uUrRbBfFtT]{1,2})(?=''')", String.Literal, "fstring-single-multiline"),
            (r'([uUrRbBfFtT]{1,2})(?=""")', String.Literal, "fstring-double-multiline"),

            # One line fstring
            (r"([uUrRbBfFtT]{1,2})(?=')", String.Literal, "fstring-single-oneline"),
            (r'([uUrRbBfFtT]{1,2})(?=")', String.Literal, "fstring-double-oneline"),

            # Numbers
            (r'\d[\d_.]*j\b', Number.Complex),
            (r'\d[\d_.]*\b', Number.Float),
            (r'\d[\d_]*\b', Number.Int),
            (r'0[xX][_0-9a-fA-F]+\b', Number.Hexadecimal),
            (r'0b[_01]+\b', Number.Binary),

            # Builtins
            from_list(list_builtins, Keyword.Builtin, suffix=r'\b'),

            # Keywords
            from_list([kw for kw in keyword.kwlist if not kw[0].isupper()], Keyword, suffix=r'\b'),
            from_list(['True', 'False', 'None'], Keyword.Constant, suffix=r'\b'),

            # Soft-Keywords (ignore _ for simplicity)
            (r'^([ \t]*)(match|case)\b', bygroups(Whitespace, Keyword)), # TODO improve this

            # Operators
            from_list(operator_list, Operator),

            # Regular name
            (uni_name, Name),

            # Punctuation
            (re.escape('...'), Punctuation),
            (rf'(\.)({uni_name})', bygroups(Punctuation, Name.Attribute)),
            (r'[;:,]',Punctuation),
            (r'[ \t]+', Whitespace),

            # Invalid specifiers
            (r'\w+\b', Syntax.Invalid), # Invalid name
            (r'.+?', Syntax.Invalid), # Default is case nothing else matches
        ],
        "string-single-multiline": [
            # Search for begining and end of string
            (r"'''.*?'''", SString.Multiline, '#pop'),
            # Search for begining and end of line
            (r"'''.*?\Z", SString.Multiline),
            # Search for end of string
            (r".*?'''", SString.Multiline, '#pop'),
            # If previous do not match, whole line is string. Keep going.
            (r".*?\Z", SString.Multiline),
        ],
        "string-double-multiline": [
            # Same as string-single-multiline
            (r'""".*?"""', SString.Multiline, '#pop'),
            (r'""".*?\Z', SString.Multiline),
            (r'.*?"""', SString.Multiline, '#pop'),
            (r'.*?\Z', SString.Multiline),
        ],
        "string-single-oneline": [
            # Search for begining and end of string
            (r"'.*?'", SString.Oneline, '#pop'),
            # Search for begining and end of line with line continuation \
            (r"'.*?\\[ \t]*\Z", SString.Oneline),
            # Search for begining and end of line without line continuation
            (r"'.*?\Z", SString.Oneline.Unterminated, '#pop'),
            # Search for end of string (continue from line continuation)
            (r".*?'", SString.Oneline, '#pop'),
            # If previous do not match, unterminated string.
            (r".*?\Z", SString.Oneline.Unterminated, '#pop'),
        ],
        "string-double-oneline": [
            # Same as string-single-oneline
            (r'".*?"', SString.Oneline, '#pop'),
            (r'".*?\\[ \t]*\Z', SString.Oneline),
            (r'".*?\Z', SString.Oneline.Unterminated, '#pop'),
            (r'.*?"', SString.Oneline, '#pop'),
            (r'.*?\Z', SString.Oneline.Unterminated, '#pop'),
        ],
        "expression-fstring": [
            (r'![ars]', FString.Format.Specifier), # !r !s or !a
            (r':.*?(?=\})', FString.Format.Specifier, '#pop'), # {... :.2f}
            (r'(?=\})', None, '#pop'), # todo this could be better : f"{{}}" is an issue
            include("expression"),
        ],
        "fstring-single-multiline": [
            # Search for formatting cell
            # ((?!''').)* is here to ensure that a cell isn't found out
            # of the string
            (r"'''((?!''').)*?\{", FString.Multiline, "expression-fstring"),
            # In case of multiple formatting cells, or cell after new line
            (r"\}?((?!''').)*?\{", FString.Multiline, "expression-fstring"),
            # Search for end of cell and end of string
            (r"\}.*?'''", FString.Multiline, '#pop'),
            # Search for end of cell and no end of string
            (r"\}.*?\Z", FString.Multiline),
            # Search for beginning and end of string (no formatting cell)
            (r"'''.*?'''", FString.Multiline, '#pop'),
            # If previous do not match, whole line is string. Keep going.
            (r".*?\Z", FString.Multiline),
        ],
        "fstring-double-multiline": [
            # Same as fstring-single-multiline
            (r'"""((?!""").)*?\{', FString.Multiline, "expression-fstring"),
            (r'\}?((?!""").)*?\{', FString.Multiline, "expression-fstring"),
            (r'\}.*?"""', FString.Multiline, '#pop'),
            (r'\}.*?\Z', FString.Multiline),
            (r'""".*?"""', FString.Multiline, '#pop'),
            (r'.*?\Z', FString.Multiline),
        ],
        "fstring-single-oneline": [
            # Search for formatting cell
            (r"'((?!').)*?\{", FString.Oneline, "expression-fstring"),
            # In case of multiple formatting cells
            (r"\}((?!').)*?\{", FString.Oneline, "expression-fstring"),
            # Search for begining and end of string
            (r"'.*?'", FString.Oneline, '#pop'),
            # Search for end of string
            (r".*?'", FString.Oneline, '#pop'),
            # Search for line continuation
            (r'.*?\\[ \t]*\Z', FString.Oneline),
            # If previous do not match, whole line is string. pop.
            (r'.*?\Z', FString.Oneline, '#pop'),
        ],
        "fstring-double-oneline": [
            # Same as fstring-single-oneline
            (r'"((?!").)*?\{', FString.Oneline, "expression-fstring"),
            (r'\}((?!").)*?\{', FString.Oneline, "expression-fstring"),
            (r'.*?"', FString.Oneline, '#pop'),
            (r'.*?\\[ \t]*\Z', FString.Oneline),
            (r'.*?\Z', FString.Oneline, '#pop'),
        ]
    }

if __name__ == "__main__":


    lexer = PythonLexer()
    # Parse itself, as a test
    with open("python_lexer.py") as f:
        for t in lexer.parse(f.read()):
            if t.type == Syntax.Invalid:
                print(t.type, ' ', t.text)