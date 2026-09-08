"""Actual NVIDIA Mark v2.3 ONNX inference; independent browser adapter.

Audio windowing / output order follows NVIDIA's MIT SDK and Apache-2.0
training framework. This adapter does not claim full SDK postprocessing parity.
"""
import json
import math
import time
import os
import sys
from pathlib import Path
import numpy as np
import onnxruntime as ort
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'vendor/models/mark-v2.3'

class Engine:
    def __init__(self):
        self.dll_handles = []
        if os.name == 'nt':
            for folder in (Path(sys.prefix) / 'Lib/site-packages/nvidia').glob('*/bin'):
                self.dll_handles.append(os.add_dll_directory(str(folder)))
                os.environ['PATH'] = str(folder) + os.pathsep + os.environ.get('PATH', '')
        if hasattr(ort, 'preload_dlls') and 'CUDAExecutionProvider' in ort.get_available_providers():
            ort.preload_dlls(directory='')
        options = ort.SessionOptions()
        options.intra_op_num_threads = 6
        options.log_severity_level = 3
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if 'CUDAExecutionProvider' in ort.get_available_providers() else ['CPUExecutionProvider']
        self.session = ort.InferenceSession(str(MODEL / 'network.onnx'), sess_options=options, providers=providers)
        self.info = json.loads((MODEL / 'network_info.json').read_text())
        self.data = np.load(MODEL / 'model_data.npz')
        self.shapes = self.data['shapes_matrix_skin'].reshape(272, -1)
        self.mean = self.data['shapes_mean_skin']
        emo = np.load(MODEL / 'implicit_emo_db.npz')
        idx = list(emo['emo_spec_names']).index(b'g2a_neutral')
        self.implicit = emo['emo_db'][int(emo['emo_spec_start'][idx]) + 33]

    def run(self, audio, sr=16000, emotion='neutral', fps=30):
        audio = np.asarray(audio, np.float32)
        if audio.ndim == 2:
            audio = audio.mean(axis=1)
        if not len(audio) or not np.isfinite(audio).all():
            raise ValueError('音频为空或包含无效数据')
        if sr != 16000:
            from scipy.signal import resample_poly
            divisor = math.gcd(int(sr), 16000)
            audio = resample_poly(audio, 16000 // divisor, int(sr) // divisor).astype(np.float32)
        audio = np.clip(audio, -1, 1)
        # Same centered 8320-sample window as network_info.json; zero padding.
        frames = int(math.ceil(len(audio) / 16000 * fps))
        padded = np.pad(audio, (4160, 8320))
        emo = np.zeros(26, np.float32)
        emo[:16] = self.implicit
        if emotion != 'neutral':
            emo[16 + self.info['params']['explicit_emotions'].index(emotion)] = 1
        results = []
        start = time.perf_counter()
        for first in range(0, frames, 16):
            indices = [round(i * 16000 / fps) for i in range(first, min(first + 16, frames))]
            inputs = np.stack([padded[t:t+8320] for t in indices])[:, None, :]
            result = self.session.run(None, {'input': inputs, 'emotion': np.tile(emo, (len(indices), 1, 1))})[0]
            results.append(result[:, 0, :])
        coeffs = np.concatenate(results).astype(np.float32)
        if not np.isfinite(coeffs).all():
            raise RuntimeError('模型输出包含无效数值')
        return audio, coeffs, {'model': 'NVIDIA Audio2Face-3D v2.3 Mark', 'runtime': f'ONNX Runtime {ort.__version__}',
            'providers': self.session.get_providers(), 'inference_seconds': round(time.perf_counter()-start, 3),
            'duration': len(audio)/16000, 'frames': frames, 'fps': fps, 'emotion': emotion,
            'window_samples': 8320, 'lookahead_seconds': 0.26,
            'postprocessing': 'PCA reconstruction; no full SDK regional smoothing, blendshape solve or eye/jaw renderer'}

    def export(self, audio, sr, emotion, target, name):
        target = Path(target)
        target.mkdir(parents=True, exist_ok=True)
        audio, coeffs, report = self.run(audio, sr, emotion)
        # Compress this actual coefficient sequence by SVD; no procedural mouth motion.
        base = coeffs[:, :272].mean(0)
        u, singular, vt = np.linalg.svd(coeffs[:, :272] - base, full_matrices=False)
        rank = min(24, len(singular))
        weights = (u[:, :rank] * singular[:rank]).astype('<f4')
        # Full 61,520-vertex topology is preserved for the surface renderer.
        basis = (vt[:rank] @ self.shapes).reshape(rank, -1, 3)
        mean = (base @ self.shapes).reshape(-1, 3) + self.mean
        scales = np.maximum(np.max(np.abs(basis), axis=(1,2)) / 32760, 1e-10).astype('<f4')
        quantized = np.round(basis / scales[:, None, None]).astype('<i2')
        data = mean.astype('<f4').tobytes() + scales.tobytes() + quantized.tobytes() + weights.tobytes()
        (target / f'{name}.bin').write_bytes(data)
        sf.write(target / f'{name}.wav', audio, 16000, subtype='PCM_16')
        report.update({'vertices': len(mean), 'rank': rank, 'motion_file': f'{name}.bin', 'audio_file': f'{name}.wav',
            'compression': 'per-clip SVD + int16 basis; full vertex topology',
            'coefficient_variance_retained': float(np.sum(singular[:rank]**2)/max(np.sum(singular**2), 1e-20)),
            'coefficient_motion_max': float(np.max(np.ptp(coeffs[:, :272], axis=0)))})
        (target / f'{name}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        np.save(target / f'{name}.coeffs.npy', coeffs)
        return report

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('audio')
    parser.add_argument('--emotion', default='neutral')
    parser.add_argument('--name', default='custom')
    parser.add_argument('--output', default=str(ROOT / 'demo/assets'))
    args = parser.parse_args()
    audio, sr = sf.read(args.audio, dtype='float32')
    print(json.dumps(Engine().export(audio, sr, args.emotion, args.output, args.name), ensure_ascii=False, indent=2))
