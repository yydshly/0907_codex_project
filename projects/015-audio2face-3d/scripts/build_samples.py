import json
from pathlib import Path
import soundfile as sf
from inference import Engine, ROOT

engine = Engine()
reports = []
for sample in ['hello', 'phonemes']:
    audio, sr = sf.read(ROOT / f'demo/assets/{sample}-zh.wav', dtype='float32')
    for emotion in ['neutral', 'joy', 'anger']:
        name = f'{sample}-{emotion}'
        report = engine.export(audio, sr, emotion, ROOT / 'demo/assets', name)
        reports.append(report)
        print(name, json.dumps(report, ensure_ascii=False), flush=True)
(ROOT / 'notes/inference-results.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
