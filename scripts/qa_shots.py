"""Print the shot list (JSON) that short_qa.py needs, computed from the same word timings the picture and the sound use."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
words = json.load(open(os.path.join(HERE, "..", "remotion", "src", "videos", "okene", "words.json")))
w = {x["w"].lower().strip(".,"): x for x in words}
fr = lambda t: round(t * 30)
cabin = fr(w["without"]["s"] - 2 / 30)       # same formulas as remotion/src/videos/okene/story.ts
sea = fr(w["may"]["s"] - 2 / 30)
total = round((words[-1]["e"] + 0.5) * 30)
print(json.dumps({"shots": [{"id": 1, "a": 0, "b": cabin}, {"id": 2, "a": cabin, "b": sea}, {"id": 3, "a": sea, "b": total}], "flash": [sea, sea + 4]}))
