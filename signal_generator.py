# signal_generator.py

# Generate floating-point samples of a waveform. A synthesizer.

class SignalGenerator:
    def __init__(self, sample_rate:int, freq:float):
        self._sample_rate:int
        self._freq:float

        self.__samples_elapsed:int

        self.set_sample_rate(sample_rate)
        self.set_freq(freq)
    
    def next_sample(self) -> float:
        # Get current waveform time.
        time = self.__samples_elapsed / self._sample_rate
        wave_position = time * self._freq % 1
        
        # Subclass handles sample generation
        sample = self._next_sample_internal(wave_position)

        # Progress time.
        self.__samples_elapsed += 1

        return sample

    def _next_sample_internal(self, wave_position:float) -> float:
        return 0.0

    def set_freq(self, freq:float):
        self._freq = freq

    def set_sample_rate(self, sample_rate:int):
        self._sample_rate = sample_rate
        self.reset()

    def reset(self):
        self.__samples_elapsed = 0

class PulseGenerator(SignalGenerator):
    def __init__(self, sample_rate:int, freq:float, pulse_percent:float):
        self._pulse_percent = pulse_percent
        super().__init__(sample_rate, freq)

    def _next_sample_internal(self, wave_position:float) -> float:
        return 1 if wave_position < self._pulse_percent else -1