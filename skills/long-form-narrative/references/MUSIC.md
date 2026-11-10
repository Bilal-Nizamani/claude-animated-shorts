# Music under a long-form video: measured from separated music stems

Source: the first 2 minutes of each of the 4 long-form videos, with the music split from the voice by Demucs (htdemucs). Numbers only; no music or titles are stored. **Four videos, 2 minutes each**: very small sample, so ranges are loose. Tempo and key are estimates (the tempo estimator snaps to a coarse grid; 99.4 bpm appears twice).

| measure | p10 | median | p90 | what it means |
|---|---|---|---|---|
| tempo (bpm) | 99 | 104 | 123 | 99-129 range, mostly about 100-108 |
| pulse strength (0-1) | 0.11 | 0.24 | 0.40 | a soft pulse is present in two videos (0.33, 0.44) |
| note onsets per second | 2.8 | 3.4 | 3.9 | gentle, a little busier than shorts |
| voice over music (dB) | 10.3 | 12.0 | 13.2 | the bed is closer to the voice than in shorts |
| ducking under words (dB) | 1.6 | 2.9 | 3.1 | slight dip while the voice speaks |
| music loudness alone (LUFS) | -29.0 | -27.7 | -26.5 | about 5 dB louder than a short's bed |
| brightness, spectral centre (Hz) | 1030 | 1120 | 1260 | warmer / darker than shorts |
| 90% of energy below (Hz) | 2900 | 3500 | 4200 | |
| harmonic over percussive (dB) | 5.0 | 7.1 | 9.6 | very sustained, almost no percussion |
| stereo side over mid (dB) | -7.6 | -5.7 | -3.6 | wider than shorts: a spacious bed |

**Key / mode:** 2 major, 2 minor (B major, E minor, D major, D# minor): both occur; the sound is warm and sustained, so mode matters less than texture.

**Spectrum of the bed** (median relative level): sub 30-120 Hz -2.6 dB, low 120-400 Hz -6.1, mid 400-2000 Hz -10.6, high 2-6 kHz -21.8, air -26.5. Bass-heavy, soft top: a dark warm pad.

**Timing:** music starts 0-1 s before or with the first word (median 0.2 s) and runs to the end of the clip.

**Over the whole video** (from the mixed audio in v1, since the stems cover only 2 minutes): the bed stays within about +-0.7 dB through the video and fades about 4.6 dB in the last tenth; 0.4-0.9 s of music after the last word, and in two videos the bed ends in silence.

## Recipe for a bed
- 100-108 bpm, warm sustained pad with slow-moving chords and a few soft plucks (about 3 onsets per second), almost no percussion (a soft pulse is fine).
- Voice 10-13 dB above the bed; let the bed dip 2-3 dB under speech (side-chain compression, slow release) if you can; otherwise keep it constant and a little lower (12-13 dB).
- Darker than a short's bed (centre about 1.1 kHz), wider stereo, more low end.
- Constant through the video, fade 3-4 dB in the last tenth, end 0.5 s after the last word (plus a tail if there is an end screen).
- Master -12.4 LUFS, true peak <= -1.2 dBTP.
