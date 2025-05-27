import re
from collections import defaultdict
from dataclasses import dataclass

if __name__ == "__main__":
    from tokens import _token_type, Token
else:
    from .tokens import _token_type, Token


# Utils
def bygroups(*args):
    return tuple(args)

@dataclass
class from_list:
    list: list[str]
    ttype: _token_type
    prefix: str = ""
    suffix: str = ""

    def to_pattern(self):
        return [
            (self.prefix + word + self.suffix, self.ttype, None)
            for word in self.list
        ]

@dataclass
class include:
    state_name: str

def combination(*states):
    name = '-'.join(states)
    return {name: [include(state) for state in states]}

def default(next_state):
    # Always matches, doesn't yield a token and go to next_state
    return ("", tuple(), next_state)

class Lexer:

    states = dict()

    def __init__(self):
        self.process_states()

    def parse(self, code: str, stack=("root",)):
        pos = 0
        stack = list(stack)
        while pos < len(code):
            match, token_type, next_state = self.find_match(code, stack[-1], pos)
            if match is None:
                pos += 1
            else:
                if token_type is not None:
                    if isinstance(token_type, tuple):
                        for i, ttype in enumerate(token_type):
                            if match.group(i+1) != "":
                                yield Token(ttype, pos + match.start(i+1), match.group(i+1))
                    else:
                        if match.group(0) != "":
                            yield Token(token_type, pos, match.group(0))
                if next_state is not None:
                    if next_state == "#pop":
                        stack.pop()
                    elif next_state == "#push":
                        stack.append(stack[-1])
                    else:
                        stack.append(next_state)
                pos += match.end(0)

    def find_match(self, code, current_state, pos):
        for case, token_type, next_state in self.processed_states[current_state]:
            match = re.match(case, code[pos:])
            if match is not None:
                return match, token_type, next_state
        return None, token_type, next_state

    def process_states(self):
        self.processed_states = defaultdict(list)
        includes = []
        for state in self.states.keys():
            for case in self.states[state]:
                # Inludes are memorized to be dealt with at the end
                if isinstance(case, include):
                    self.processed_states[state].append(case)
                    includes.append((state, case))

                # Create from lists of possible words
                elif isinstance(case, from_list):
                    self.processed_states[state].extend(case.to_pattern())

                # Pad states to len 3 with None
                else:
                    match len(case):
                        case 1:
                            self.processed_states[state].append(
                                (re.compile(case[0], flags=re.MULTILINE), None, None)
                            )
                        case 2:
                            self.processed_states[state].append(
                                (re.compile(case[0], flags=re.MULTILINE), case[1], None)
                            )
                        case 3:
                            self.processed_states[state].append(
                                (re.compile(case[0], flags=re.MULTILINE), case[1], case[2])
                            )
                        case _:
                            raise ValueError()

        # Process includes at the end, to prevent partial copies
        while includes != []:
            state, inc = includes.pop()
            pats = self.processed_states[state]
            i = pats.index(inc)
            self.processed_states[state] = pats[:i] + self.processed_states[inc.state_name] + pats[i+1:]
            for case, _, _ in self.processed_states[inc.state_name]:
                if isinstance(case, include):
                    includes.append((state, case))




if __name__ == "__main__":
    Root = _token_type(name = "Test")

    class Tester(Lexer):
        states = {
            "root": [
                (r"\s+",), # Match but don't add token
                from_list(["spy", "queen"], Root.Word.Job),
                (r"[A-Z][a-z]*", Root.Word.Name, "name"),
                (r"[a-z]+", Root.Word),
                include("number"),
                (r"[\.,\:;\?\!]", Root.Punctuation),
            ],
            "name": [
                (r"[A-Z][a-z]*\b", Root.Word.Surname, "#pop"),
                default("#pop"),
            ],
            "number": [
                (r"\d+", Root.Number.Integer),
            ]
        }

    lexer = Tester()
    print(list(lexer.parse("James Bond, spy for the queen")))
    print(list(lexer.parse("James, 1 12 spy")))