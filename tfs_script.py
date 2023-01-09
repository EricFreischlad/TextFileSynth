# tfs_script.py

# The scripting language definition for TFS.

# Example: "a8 b8 c+16 _16 d16 _16 e8 f+8 g+16 _16 > a4"
# letter = note
# underscore = rest
# number = beat division between 1 and 64
# each ~ after number = another of that duration (a16~~ is a dotted eighth on A) (a1~~~ is a 4 measure hold on A)
# + or - = previous note is sharp or flat
# < or > = octave down or up

from enum import Enum
from tfs_env import TFSEnvironment

class TokenType(Enum):
    NOTE_LETTER = 0 # value is str letter (same as raw)
    UNDERSCORE = 1  # value is empty
    NUMBER = 2      # value is int value
    TILDES = 3      # value is count
    PLUS_MINUS = 4  # value is True if plus, False if minus
    GT_LT = 5       # value is True if GT, False if LT

class Token:
    script_index:int
    raw_script:str
    token_type:TokenType
    value:object

class Parser:
    __NOTE_NUM_OFFSETS = {
        'a': 9,
        'b': 11,
        'c': 0,
        'd': 2,
        'e': 4,
        'f': 5,
        'g': 7,
    }
    
    MAX_OCTAVE = 9
    MIN_OCTAVE = 0

    def __init__(self, tokens:list, environment:TFSEnvironment):
        self.__env = environment
        self.__tokens = tokens
        self.error_msg = "Incomplete"

        self.__octave = 5

        self.__current = 0

        self.samples = []

        self.success = self.__try_parse_tokens()

    def __try_parse_tokens(self):
        while not self.__is_at_end():
            if not self.__parse_next_token():
                return False
        
        self.error_msg = "Text parsed successfully"
        return True

    def __parse_next_token(self) -> bool:
        t = self.__advance()

        if t.token_type == TokenType.NOTE_LETTER:
            if not self.__note(t):
                return False
        elif t.token_type == TokenType.UNDERSCORE:
            if not self.__rest():
                return False
        elif t.token_type == TokenType.GT_LT:
            self.__octave_change(t)
        else:
            self.error_msg = f"Unexpected token at index {self.__current}: {t.token_type.name} (Expected: Note, rest, or octave change)"
            return False
        
        return True

    def __is_at_end(self) -> bool:
        return self.__current >= len(self.__tokens)

    def __advance(self) -> Token:
        self.__current += 1
        return self.__tokens[self.__current - 1]

    def __try_peek(self):
        if self.__current < len(self.__tokens):
            return True, self.__tokens[self.__current]
        return False, None

    def __note(self, token:Token) -> bool:
        note_num = 69
        divisor = 1
        duration = 1

        # Parse note letter.
        note_letter = str(token.value)
        if note_letter in Parser.__NOTE_NUM_OFFSETS.keys():
            note_num = (self.__octave * 12) + Parser.__NOTE_NUM_OFFSETS[note_letter]
        
        # Parse sharp or flat, if given.
        found, token = self.__try_peek()
        if found and token.token_type == TokenType.PLUS_MINUS:
            sharp_flat = self.__advance()
            if sharp_flat.value:    # Bool
                note_num += 1
            elif not sharp_flat.value:
                note_num -= 1

        # Parse measure divisor.
        found, token = self.__try_peek()
        if found and token.token_type == TokenType.NUMBER:
            number = self.__advance()
            if number.value != 0:
                divisor = number.value
            else:
                # Measure divisor must not be 0.
                self.error_msg = f"Measure divisor may not be 0."
                return False
        else:
            # Measure divisor required.
            self.error_msg = f"Unexpected token after note letter at index {self.__current}: {token.token_type.name if token else 'NONE'} (Expected: Measure divisor number)"
            return False
        
        # Parse extended duration.
        if not self.__is_at_end():
            found, token = self.__try_peek()
            if found and token.token_type == TokenType.TILDES:
                tildes = self.__advance()
                duration += tildes.value

        # Generate the samples.
        self.samples.extend(self.__env.note(note_num, divisor, duration))

        return True
    
    def __rest(self) -> bool:
        divisor = 1
        duration = 1

        # Parse measure divisor.
        found, token = self.__try_peek()
        if found and token.token_type == TokenType.NUMBER:
            number = self.__advance()
            if number.value != 0:
                divisor = number.value
            else:
                # Measure divisor must not be 0.
                self.error_msg = f"Measure divisor may not be 0."
                return False
        else:
            # Measure divisor required.
            self.error_msg = f"Unexpected token after rest at index {self.__current}: {token.token_type.name if token else 'NONE'} (Expected: Measure divisor number)"
            return False
        
        # Parse extended duration.
        if not self.__is_at_end():
            found, token = self.__try_peek()
            if found and token.token_type == TokenType.TILDES:
                tildes = self.__advance()
                duration += tildes.value

        # Generate the samples.
        self.samples.extend(self.__env.rest(divisor, duration))

        return True

    def __octave_change(self, token:Token):
        if token.value:     # bool
            # Raise the octave by one, respecting the max octave.
            self.__octave = min(self.MAX_OCTAVE, self.__octave + 1)
        elif not token.value:
            # Lower the octave by one, respecting the min octave.
            self.__octave = max(self.MIN_OCTAVE, self.__octave - 1)

class Scanner:
    def __init__(self, text:str):
        self.__text = text
        self.error_msg = "Incomplete"
        self.tokens = []
        self.__current = 0

        self.success = self.__try_scan_tokens()

    def __try_scan_tokens(self):
        while not self.__is_at_end():
            self.__start_of_token = self.__current

            if not self.__scan_next_token():
                return False
        
        self.error_msg = "Text scanned successfully"
        return True

    def __scan_next_token(self) -> bool:
        c = self.__advance()

        if c == ' ' or c == '\n' or c == '\t' or c == '\r':
            pass
        elif c == '#':
            self.__comment()
        elif c == '~':
            self.__tildes()
        elif c == '_':
            self.__add_token(TokenType.UNDERSCORE, None)
        elif c == '+':
            self.__add_token(TokenType.PLUS_MINUS, True)
        elif c == '-':
            self.__add_token(TokenType.PLUS_MINUS, False)
        elif c == '>':
            self.__add_token(TokenType.GT_LT, True)
        elif c == '<':
            self.__add_token(TokenType.GT_LT, False)
        elif c.isnumeric():
            self.__number()
        elif c in "abcdefg":
            self.__add_token(TokenType.NOTE_LETTER, c)
        else:
            self.error_msg = f"Unrecognized character at index {self.__current}: \'{c}\'"
            return False
            
        return True

    def __is_at_end(self) -> bool:
        return self.__current >= len(self.__text)

    def __add_token(self, token_type, value:object):
        token = Token()
        token.script_index = self.__start_of_token
        token.raw_script = self.__get_substring()
        token.token_type = token_type
        token.value = value
        
        self.tokens.append(token)

    def __advance(self) -> str:
        self.__current += 1
        return self.__text[self.__current - 1]
    
    def __peek(self) -> str:
        return self.__text[self.__current]
    
    def __get_substring(self) -> str:
        return self.__text[self.__start_of_token : self.__current]

    def __comment(self):
        while not self.__is_at_end():
            c = self.__advance()

            # If newline, UNIX line ending
            if c == '\n':
                # Comment is complete.
                break

            # If carriage return, assume Windows line ending
            if c == '\r':
                # Consume expected newline
                self.__advance()
                # Comment is complete
                break
    
    def __number(self):
        while not self.__is_at_end():
            c = self.__peek()

            if not c.isnumeric():
                break

            self.__advance()

        self.__add_token(TokenType.NUMBER, int(self.__get_substring()))

    def __tildes(self):
        while not self.__is_at_end():
            c = self.__peek()

            if c != '~':
                break

            self.__advance()

        self.__add_token(TokenType.TILDES, len(self.__get_substring()))