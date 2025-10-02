import mido
import random
from mido import MidiFile, MidiTrack, Message
import os
import tempfile


class MelodyGenerator:
    def __init__(self):
        self.base_notes = {
            'C': 60, 'C#': 61, 'D': 62, 'D#': 63, 'E': 64, 'F': 65,
            'F#': 66, 'G': 67, 'G#': 68, 'A': 69, 'A#': 70, 'B': 71
        }

        self.scale_patterns = {
            'Major': [0, 2, 4, 5, 7, 9, 11, 12],
            'Natural Minor': [0, 2, 3, 5, 7, 8, 10, 12],
            'Harmonic Minor': [0, 2, 3, 5, 7, 8, 11, 12],
            'Pentatonic Major': [0, 2, 4, 7, 9, 12],
            'Pentatonic Minor': [0, 3, 5, 7, 10, 12],
            'Dorian': [0, 2, 3, 5, 7, 9, 10, 12],
            'Phrygian': [0, 1, 3, 5, 7, 8, 10, 12],
            'Lydian': [0, 2, 4, 6, 7, 9, 11, 12],
            'Mixolydian': [0, 2, 4, 5, 7, 9, 10, 12],
            'Aeolian': [0, 2, 3, 5, 7, 8, 10, 12],
            'Locrian': [0, 1, 3, 5, 6, 8, 10, 12]
        }
        
        self.contours = ['ascending', 'descending', 'arch', 'inverted_arch', 'static']
        
        self.durations = {
            'whole': 1920,
            'half': 960,
            'quarter': 480,
            'eighth': 240,
            'sixteenth': 120
        }

    def get_scale(self, key, mode, octaves=2):
        base_note = self.base_notes[key]
        if isinstance(mode, list):
            pattern = mode
        elif mode in self.scale_patterns:
            pattern = self.scale_patterns[mode]
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        scale = []
        for octave in range(octaves):
            scale.extend([base_note + interval + (12 * octave) for interval in pattern])
        
        return scale

    def apply_melodic_rules(self, current_note, scale, previous_notes, contour='arch', max_leap=7):
        if not previous_notes:
            stable_degrees = [0, 2, 4]
            return scale[random.choice(stable_degrees)]
        
        current_index = scale.index(current_note) if current_note in scale else len(scale) // 2
        scale_length = len(scale)

        total_notes = len(previous_notes) + 1
        CONTOUR_RESOLUTION = 16.0
        contour_position = total_notes / CONTOUR_RESOLUTION
        
        if contour == 'ascending':
            target_area = int(scale_length * contour_position)
        elif contour == 'descending':
            target_area = int(scale_length * (1 - contour_position))
        elif contour == 'arch':
            if contour_position < 0.5:
                target_area = int(scale_length * (contour_position * 2))
            else:
                target_area = int(scale_length * (2 - contour_position * 2))
        elif contour == 'inverted_arch':
            if contour_position < 0.5:
                target_area = int(scale_length * (1 - contour_position * 2))
            else:
                target_area = int(scale_length * (contour_position * 2 - 1))
        else:
            target_area = scale_length // 2
        
        STEP_PROBABILITY = 0.7
        STEP_OPTIONS = [-2, -1, 1, 2]
        MIN_LEAP = 3
        MAX_LEAP = 5

        if random.random() < STEP_PROBABILITY:
            next_index = current_index + random.choice(STEP_OPTIONS)
        else:
            leap_size = random.randint(MIN_LEAP, min(MAX_LEAP, max_leap))
            direction = 1 if target_area > current_index else -1
            next_index = current_index + (leap_size * direction)
        
        next_index = max(0, min(scale_length - 1, next_index))
        
        if len(previous_notes) >= 2:
            if scale[next_index] == previous_notes[-1] == previous_notes[-2]:
                next_index = (next_index + random.choice([-2, -1, 1, 2])) % scale_length
        
        if len(previous_notes) >= 1:
            prev_interval = abs(current_note - previous_notes[-1])
            if prev_interval > 4:
                if current_note > previous_notes[-1]:
                    next_index = max(0, current_index - random.randint(1, 2))
                else:
                    next_index = min(scale_length - 1, current_index + random.randint(1, 2))
        
        return scale[next_index]

    def get_rhythmic_pattern(self, measures=4, pattern_type='balanced'):
        rhythms = []
        total_ticks = measures * 1920
        
        if pattern_type == 'balanced':
            duration_weights = [0.1, 0.4, 0.3, 0.15, 0.05]
        elif pattern_type == 'syncopated':
            duration_weights = [0.05, 0.2, 0.5, 0.2, 0.05]
        elif pattern_type == 'legato':
            duration_weights = [0.2, 0.5, 0.2, 0.1, 0.0]
        else:
            duration_weights = [0.0, 0.1, 0.3, 0.5, 0.1]
        
        duration_options = list(self.durations.values())
        
        current_tick = 0
        while current_tick < total_ticks:
            duration = random.choices(duration_options, weights=duration_weights)[0]
            
            if current_tick + duration > total_ticks:
                duration = total_ticks - current_tick
            
            rhythms.append(duration)
            current_tick += duration
            
            if random.random() < 0.1 and current_tick < total_ticks:
                rest_duration = random.choice([self.durations['sixteenth'], self.durations['eighth']])
                if current_tick + rest_duration <= total_ticks:
                    rhythms.append(-rest_duration)
                    current_tick += rest_duration
        
        return rhythms

    DEFAULT_KEY = 'C'
    DEFAULT_MODE = 'Major'
    DEFAULT_MEASURES = 4
    DEFAULT_BPM = 120

    def generate_melody(self, key: str = DEFAULT_KEY, mode: str = DEFAULT_MODE, 
                   measures: int = DEFAULT_MEASURES, bpm: int = DEFAULT_BPM,
                   contour: str = 'arch', rhythm_type: str = 'balanced', 
                   max_leap: int = 7, output_path: str = None) -> str:

        mid = MidiFile(ticks_per_beat=480)
        track = MidiTrack()
        mid.tracks.append(track)

        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo))

        scale = self.get_scale(key, mode, octaves=2)
        
        rhythms = self.get_rhythmic_pattern(measures, rhythm_type)
        
        stable_degrees = [0, 2, 4]
        current_note = scale[random.choice(stable_degrees)]
        previous_notes = []

        for duration in rhythms:
            if duration < 0:
                track.append(Message('note_off', note=0, velocity=0, time=abs(duration)))
                continue
                
            current_note = self.apply_melodic_rules(
                current_note, scale, previous_notes, contour, max_leap
            )
            previous_notes.append(current_note)
            
            if len(previous_notes) < len(rhythms) * 0.25:
                velocity = random.randint(85, 100)
            elif len(previous_notes) < len(rhythms) * 0.75:
                velocity = random.randint(95, 115)
            else:  # End
                velocity = random.randint(80, 95)
            
            track.append(Message('note_on', note=current_note, velocity=velocity, time=0))
            track.append(Message('note_off', note=current_note, velocity=0, time=duration))

        if previous_notes:
            final_note = scale[random.choice([0, 4])]
            track.append(Message('note_on', note=final_note, velocity=80, time=0))
            track.append(Message('note_off', note=final_note, velocity=0, time=self.durations['quarter']))

        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f'melody_{key}_{mode}_{bpm}bpm.mid')

        mid.save(output_path)
        return output_path