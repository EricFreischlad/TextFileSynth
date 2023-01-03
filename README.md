# TextFileSynth
Create an audio file from commands in a .TXT document.

# Command Syntax
- REQUIRED: a lower case letter ('a' through 'g') to represent the note name
  - ALTERNATIVELY: an underscore (_) to represent a rest
- OPTIONAL: a plus (+) or minus (-) to represent a sharp or flat, respectively
- REQUIRED: an integer value representing the duration for the note to play, as a divisor of a full 4/4 measure
  - Example: 1 = whole note, 2 = half note, 4 = quarter note, 8 = eighth note. All whole numbers greater than 0 are acceptable.
 - OPTIONAL: any number of tildes (~). each tilde represents an additional duration for the note to play.
  - Example: For a note with divisor number of 4, adding no tildes will make the note play for a quarter of a measure, adding one tilde will make it play for half a measure, adding 3 tildes will make it play for 3/4 of a measure, etc...

Blocks of characters used to define individual notes should be separated by spaces, but it is not required.
  Example: "a16 _16 b4~~ c+4"

Instead of a block of characters defining a note, greater-than (>) and less-than (<) symbols can be used to change the current octave up and down, respectively. These do not need to be used for each note. Rather, each one changes the octave for all notes after it until the next change. The default octave at the beginning of parsing is 5.
  Example: "a8 > a8 > a8 << a8"

Comments are ignored. They begin with a number sign (#) and end with the next line break.
  Example: "a8~~ # This note is played, but the rest of this line is ignored!"

The program is run with the following command arguments:
- arg0: "python"
- arg1: script name ("tfs.py")
- arg2: input TXT file name with extension ("your_input_file.txt")
- arg3: output WAV file name with extension ("your_output_file.wav")

Try the following cmd from the working directory:
python tfs.py route1.txt route1.wav
