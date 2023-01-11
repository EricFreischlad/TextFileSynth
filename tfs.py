# tfs.py

# Text File Synth. Create an audio file from commands in a .TXT file.

import sys
from tfs_env import TFSEnvironment
from tfs_script import Scanner
from tfs_script import Parser
import pywav

def __console_program():
    # Parse console command options.
    # argv[0] = "tfs.py", argv[1] = input text file path, argv[2] = output WAV file path
    argc = len(sys.argv)

    if argc < 2:
        print("No input file specified.")
        exit(1)

    input_path = sys.argv[1].strip('\"')
    output_path = ""
    if (argc > 2):
        output_path = sys.argv[2].strip('\"')
    
    # Open and read input file.
    input = ""
    try:
        with open(input_path, "rt") as f:
            input = f.read()
    except FileNotFoundError:
        print(f"Failed to open input file at: \"{input_path}\"")
        exit(1)

    # Scan input.
    scanner = Scanner(input)

    if not scanner.success:
        print(f"Scanner error: {scanner.error_msg}")
        exit(51)

    # Debug Scanned Tokens
    # for t in scanner.tokens:
    #     print(t)

    # Set up synth environment.
    SAMPLE_RATE = 44100
    FORMAT = pywav.SampleFormat.int_fmt(8)

    env = TFSEnvironment(SAMPLE_RATE)
    env.set_bpm(160)

    # Parse input.
    parser = Parser(scanner.tokens, env)

    if not parser.success:
        print(f"Parser error: {parser.error_msg}")
        exit(52)

    # Successful scan and parse.
    print("File scanned and parsed successfully.")

    # If output path is specified and valid, output to it.
    if output_path != "":
        try:
            with open(output_path, "wb") as f:
                f.write(pywav.create_from_samples_mono(SAMPLE_RATE, FORMAT, parser.samples))
                f.flush()
                print(f"Output was placed at \"{output_path}\"")
        except OSError as e:
            print(f"Unable to write to output file at \"{output_path}\": {e}")
            exit(53)
        except Exception as e:
            print(f"Unexpected exception: {e}")
            exit(54)
    else:
        print("No output file specified.")

__console_program()