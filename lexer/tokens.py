import re
from dataclasses import dataclass

class _token_type:

    _inherited = ("default_style", "style")

    def __init__(self, parent=None, name=None):
        self.parent = parent
        self.name = "Synthax" if name is None else name
        self.children = set()

    def __getattr__(self, name):
        # Create new token is first letter is capitalize (convention)
        if name[0].isupper():
            # Create new token
            new_token = _token_type(parent=self, name=name)

            # Add new token as attribute of current token
            setattr(self, name, new_token)

            # Add token to children of all parents
            p = self
            while p is not None:
                p.children.add(new_token)
                p = p.parent

            return new_token

        # Go to parent if attribute can be inherited
        elif name in self._inherited:
            if self.parent is not None:
                return getattr(self.parent, name)
            else:
                raise RecursionError(f"{name} can be inherited but was never found in token tree")

        # Default
        else:
            raise AttributeError(f"{name} is not a valid attribute of {Python.__class__.__name__}")

    def get_genealogy(self):
        if self.parent is None:
            return [self]
        return self.parent.get_genealogy() + [self]

    @property
    def full_name(self):
        return ".".join([t.name for t in self.get_genealogy()])

    def __repr__(self):
        return self.full_name

    def __call__(self, match):
        return Token(self, match.start(), match.group(0))

@dataclass
class Token:
    type: _token_type
    start: int
    text: str

    @property
    def end(self):
        return self.start + len(self.text)

    @property
    def name(self):
        return self.type.full_name

    def __repr__(self):
        return f'{self.name} : "{self.text}"'

# Define root of tokens
Syntax = _token_type()

# Aliases
Whitespace = Syntax.Whitespace
String = Syntax.String
Comment = Syntax.Comment
Keyword = Syntax.Keyword
Name = Syntax.Name
Operator = Syntax.Operator
Number = Syntax.Number



if __name__ == "__main__":
    Type = _token_type(name="Type")
    Type.default_style = "style"

    print(f"{Type.Test.default_style = }")
    print(f"{Type.Test.full_name = }")

    s = "Isaac Newton"

    t = Type.Name(re.match(r"\w+", s))

    print(t)


