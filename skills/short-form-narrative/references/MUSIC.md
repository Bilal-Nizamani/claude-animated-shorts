# Music under a short: measured from separated music stems

Source: 10 of the 16 shorts (the shortest ten), with the music split from the voice by Demucs (htdemucs, two stems). Numbers only; no music, titles or tracks are stored. Small sample: treat ranges as starting points. Tempo and key come from audio analysis and are estimates (the tempo estimator snaps to a coarse grid: 99.4 bpm appears 4 times, so read tempo as "about 95-120 bpm", not an exact value).

| measure | p10 | median | p90 | what it means |
|---|---|---|---|---|
| tempo (bpm) | 99 | 106 | 118 | moderate, unhurried |
| pulse strength (0-1) | 0.05 | 0.10 | 0.15 | no strong drum beat (one short 0.29) |
| note onsets per second | 2.4 | 3.0 | 4.0 | gentle plucks / chords, not busy |
| voice over music (dB) | 15.4 | 17.8 | 19.6 | the bed is far under the voice |
| ducking under words (dB) | -0.5 | 1.2 | 2.1 | essentially none; the bed is constant |
| music loudness alone (LUFS) | -34.6 | -32.5 | -29.6 | |
| brightness, spectral centre (Hz) | 1160 | 1500 | 1590 | warm, not bright |
| 90% of energy below (Hz) | 3200 | 3900 | 5000 | little content above 4-5 kHz |
| harmonic over percussive (dB) | 2.0 | 3.7 | 6.7 | sustained tones dominate; light percussion |
| stereo side over mid (dB) | -13.8 | -11.8 | -9.4 | fairly narrow, mostly centred |
| level change over the video | | | | -0.7 to +1.2 dB: flat |

**Key / mode:** 8 of 10 minor, 2 major. Confident keys: E minor 4, A minor 3, D minor 1, F major 1, A major 1. Minor, soft, sustained.

**Spectrum of the bed** (level of each band relative to the whole bed, median): sub 30-120 Hz -4.9 dB, low 120-400 Hz -7.8, mid 400-2000 Hz -5.1, high 2-6 kHz -11.9, air 6-11 kHz -22. Warm and mid-heavy with a roll-off; nothing sparkly.

**Timing:** the music is already playing at the first word (starts 0-0.05 s) and stops at the end of the narration (-0.05 to +0.12 s from the end). No intro, no outro tail.

## Level: two methods disagree, use a range
- Separated stems: voice about 15-20 dB above the bed (median 17.8).
- The first look at the mixed audio (v1) gave about 11 dB.
The stem method is more direct but Demucs leaks a little voice and music across stems, and loudness over the whole bed includes the gaps in the voice. **Start at 14-16 dB under the voice** (a clearly audible but light bed), then lower the bed if it competes with the words. The final level is a listening decision.

## Recipe for a bed
- Minor key (A / E / D minor), 95-120 bpm, sustained pad plus soft plucks or music-box notes, about 3 note onsets per second, no kick or snare.
- Constant level for the whole short; no ducking, no swells; start on the first word and end with the last.
- Low-pass or shelf so little energy sits above 4-5 kHz; keep stereo narrow.
- In this repo: `templates/audio/instruments.py` (`pad`, `pluck`, `musicbox`, `vibes`), or any licensed track you have the right to use.
- Master the finished mix to -11 LUFS (true peak <= -1.2 dBTP) as in the delivery map.
