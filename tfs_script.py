# tfs_script.py

# The scripting language definition for TFS.

# Example: "a8 b8 c+16 _16 d16 _16 e8 f+8 g+16 _16 > a4"
# letter = note
# underscore = rest
# number = beat division between 1 and 64
# each ~ after number = another of that duration (a16~~ is a dotted eighth on A) (a1~~~ is a 4 measure hold on A)
# + or - = previous note is sharp or flat
# < or > = octave down or up
# @ followed by number = new BPM

from tfs_env import TFSEnvironment

class TokenType:
    def __init__(self, disp_name:str):
        self.disp_name = disp_name

    def __str__(self):
        return f"TokenType({self.disp_name})"
    
    def __repr__(self) -> str:
        return self.__str__()

NOTE_LETTER = TokenType("Note Letter")
REST = TokenType("Rest")
NUMBER = TokenType("Number")
LENGTH_EXT = TokenType("Length Extension")
SHARP = TokenType("Sharp")
FLAT = TokenType("Flat")
OCT_UP = TokenType("Octave Up")
OCT_DN = TokenType("Octave Down")
BPM_CHANGE = TokenType("BPM Change")

class ScriptIndex:
    def __init__(self, line:int, column:int) -> None:
        self.line_num = line
        self.column_num = column
    
    def __str__(self) -> str:
        return f"(Ln: {self.line_num}, Col: {self.column_num})"
    def __repr__(self) -> str:
        return self.__str__()
        
class Token:

    def __init__(self):
        self.script_index:ScriptIndex
        self.raw_script:str
        self.token_type:TokenType
        self.value:object

    def __str__(self) -> str:
        return f"Token(\"{self.token_type.disp_name}\", {self.raw_script})@{self.script_index}"

    def __repr__(self) -> str:
        return self.__str__()

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

        if t.token_type == NOTE_LETTER:
            if not self.__note(t):
                return False
        elif t.token_type == REST:
            if not self.__rest(t):
                return False
        elif t.token_type in {OCT_UP, OCT_DN}:
            self.__octave_change(t)
        elif t.token_type == BPM_CHANGE:
            if not self.__bpm_change(t):
                return False
        else:
            return self.__error(f"Unexpected token at {t.script_index}: {t.token_type.disp_name} (Expected: Note, rest, octave change, or BPM change)")
        
        return True

    def __error(self, msg:str) -> False:
        self.error_msg = msg
        return False

    def __is_at_end(self) -> bool:
        return self.__current >= len(self.__tokens)

    def __advance(self) -> Token:
        self.__current += 1
        return self.__tokens[self.__current - 1]

    def __try_peek(self):
        if self.__current < len(self.__tokens):
            return True, self.__tokens[self.__current]
        return False, None

    def __optional_param(self, expected_type:TokenType):
        found, token = self.__try_peek()
        if found and token.token_type == expected_type:
            self.__advance()
            return True, token
        return False, None
    
    def __required_param(self, preceeding_token:Token, expected_type:TokenType):
        found, token = self.__try_peek()
        if found:
            if token.token_type == expected_type:
                self.__advance()
                return True, token
            else:
                self.error_msg = f"Unexpected token after {preceeding_token.token_type.disp_name} at {preceeding_token.script_index}: {token.token_type.disp_name} (Expected: {expected_type.disp_name})"
                return False, token
        else:
            self.error_msg = f"Missing token after {preceeding_token.token_type.disp_name} at {preceeding_token.script_index}. Expected: {expected_type.disp_name}"
            return False, None

    def __note(self, note_letter_token:Token) -> bool:
        note_num = 69
        divisor = 1
        duration = 1

        # Parse note letter.
        note_letter = str(note_letter_token.value)
        if note_letter in Parser.__NOTE_NUM_OFFSETS.keys():
            note_num = (self.__octave * 12) + Parser.__NOTE_NUM_OFFSETS[note_letter]
        else:
            return self.__error(f"Unrecognized note letter at {note_letter_token.script_index}: {note_letter}")
        
        # Parse sharp or flat.
        found, _ = self.__optional_param(SHARP)
        if found:
            note_num += 1
        else:
            found, _ = self.__optional_param(FLAT)
            if found:
                note_num -= 1

        # Parse measure divisor.
        found, measure_div_token = self.__required_param(note_letter_token, NUMBER)
        if not found:
            return False
        
        if measure_div_token.value > 0:
            divisor = measure_div_token.value
        else:
            # Measure divisor must be greater than 0.
            return self.__error(f"Measure divisor at {measure_div_token.script_index} must be greater than 0")
        
        # Parse length extension.
        found, length_ext_token = self.__optional_param(LENGTH_EXT)
        if found:
            duration += length_ext_token.value

        # Generate the samples.
        self.samples.extend(self.__env.note(note_num, divisor, duration))

        return True
    
    def __rest(self, rest_token:Token) -> bool:
        divisor = 1
        duration = 1

        # TODO: Consolidate this functionality with note letter functionality.

        # Parse measure divisor.
        found, measure_div_token = self.__required_param(rest_token, NUMBER)
        if not found:
            return False
        
        if measure_div_token.value > 0:
            divisor = measure_div_token.value
        else:
            # Measure divisor must be greater than 0.
            return self.__error(f"Measure divisor at {measure_div_token.script_index} must be greater than 0")
        
        # Parse length extension.
        found, length_ext_token = self.__optional_param(LENGTH_EXT)
        if found:
            duration += Token(length_ext_token).value

        # Generate the samples.
        self.samples.extend(self.__env.rest(divisor, duration))

        return True

    def __octave_change(self, token:Token):
        if token.token_type == OCT_UP:
            # Raise the octave by one, respecting the max octave.
            self.__octave = min(self.MAX_OCTAVE, self.__octave + 1)
        elif token.token_type == OCT_DN:
            # Lower the octave by one, respecting the min octave.
            self.__octave = max(self.MIN_OCTAVE, self.__octave - 1)

    def __bpm_change(self, bpm_change_token:Token):
        # Parse new BPM number.
        found, bpm_num_token = self.__required_param(bpm_change_token, NUMBER)
        if not found:
            return False
        
        if bpm_num_token.value > 0:
            self.__env.set_bpm(bpm_num_token.value)
        else:
            return self.__error(f"BPM number at {bpm_num_token.script_index} must be greater than 0.")
        
        return True

class Scanner:
    def __init__(self, text:str):
        self.__text = text
        self.error_msg = "Incomplete"
        self.tokens = []
        self.__current = 0

        self.__current_ln = 0
        self.__current_col = 0

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

        if c == ' ' or c == '\t':
            pass
        elif c in {'\r', '\n'}:
            self.__newline(c)
        elif c == '#':
            self.__comment()
        elif c == '~':
            self.__tildes()
        elif c == '_':
            self.__add_token(REST, None)
        elif c == '+':
            self.__add_token(SHARP, None)
        elif c == '-':
            self.__add_token(FLAT, None)
        elif c == '>':
            self.__add_token(OCT_UP, None)
        elif c == '<':
            self.__add_token(OCT_DN, None)
        elif c == '@':
            self.__add_token(BPM_CHANGE, None)
        elif c.isnumeric():
            self.__number()
        elif c in "abcdefg":
            self.__add_token(NOTE_LETTER, c)
        else:
            self.error_msg = f"Unrecognized character at {ScriptIndex(self.__current_ln + 1, self.__current_col + 1)}: \'{c}\'"
            return False

        return True

    def __is_at_end(self) -> bool:
        return self.__current >= len(self.__text)

    def __add_token(self, token_type, value:object):
        token = Token()
        token.raw_script = self.__get_substring()
        token.script_index = ScriptIndex(self.__current_ln + 1, self.__current_col - len(token.raw_script) + 1)
        token.token_type = token_type
        token.value = value
        
        self.tokens.append(token)

    def __advance(self) -> str:
        self.__current += 1
        self.__current_col += 1
        return self.__text[self.__current - 1]
    
    def __peek(self) -> str:
        return self.__text[self.__current]
    
    def __get_substring(self) -> str:
        return self.__text[self.__start_of_token : self.__current]

    def __newline(self, c:str):
        self.__current_col = 0
        self.__current_ln += 1

        # Consume second control character if using Windows line endings.
        if c == '\r' and self.__peek() == '\n':
            self.__advance()

    def __comment(self):
        while not self.__is_at_end():
            c = self.__advance()

            # If newline, UNIX line ending
            if c in {'\r', '\n'}:
                self.__newline(c)
                # Comment is complete.
                break
    
    def __number(self):
        while not self.__is_at_end():
            c = self.__peek()

            if not c.isnumeric():
                break

            self.__advance()

        self.__add_token(NUMBER, int(self.__get_substring()))

    def __tildes(self):
        while not self.__is_at_end():
            c = self.__peek()

            if c != '~':
                break

            self.__advance()

        self.__add_token(LENGTH_EXT, len(self.__get_substring()))