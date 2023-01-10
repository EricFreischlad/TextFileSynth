# tfs_env.py

# Text File Synth environment functions

import signal_generator

class TFSEnvironment:
    __sample_rate = 44100
    __synth:signal_generator.SignalGenerator

    __bpm = 120.0
    __gain = 0.25

    def __init__(self, sample_rate:int):
        # No checks here.
        self.__sample_rate = sample_rate
        self.__synth = signal_generator.PulseGenerator(sample_rate, 440, 0.125)

    def set_bpm(self, bpm:float):
        if bpm > 0:
            self.__bpm = bpm

    def set_gain(self, gain:float):
        if gain in range(0, 1):
            self.__gain = gain

    def __get_freq(note_num:int):
        # MIDI tuning standard from Wikipedia, baby!
        # Use a look-up table if needed.
        return 2**((note_num - 69) / 12) * 440.0

    def __get_num_samples(sample_rate:int, bpm:float, beat_divisor:int, duration:int):
        
        # Length of note in samples is: (sample rate) * (seconds per beat) * (the fraction of a beat to play)
        # For example, 3 16th notes in length (dotted eighth) at 120 BPM in a 44100 Hz environment would be: (44100) * (0.5 [60/120]) * (3/4) = 16537.5 samples (always truncate)
        return int(sample_rate * (60 / bpm) * (duration / beat_divisor)) * 4

    def note(self, note_num:int, beat_divisor:int, duration:int):
        freq = TFSEnvironment.__get_freq(note_num)
        self.__synth.set_freq(freq)
        
        num_samples = TFSEnvironment.__get_num_samples(self.__sample_rate, self.__bpm, beat_divisor, duration)
        return [self.__synth.next_sample() * self.__gain for _ in range(num_samples)]

    def rest(self, beat_divisor:int, duration:int):
        num_samples = TFSEnvironment.__get_num_samples(self.__sample_rate, self.__bpm, beat_divisor, duration)
        return [0.0 for _ in range(num_samples)]