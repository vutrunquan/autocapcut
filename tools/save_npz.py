import re
import base64
import os
import numpy as np

with open('tools/gemini-watermark-remover/src/core/embeddedAlphaMaps.js', 'r', encoding='utf-8') as f:
    c = f.read()

def get_arr(k):
    pat = rf"'{k}':\s*'([^']+)'" if '-' in k else rf"{k}:\s*'([^']+)'"
    m = re.search(pat, c)
    return np.frombuffer(base64.b64decode(m.group(1)), dtype=np.float32)

maps = {
    'alpha48': get_arr('48').reshape((48, 48)),
    'alpha96': get_arr('96').reshape((96, 96)),
    'alpha96_v2': get_arr('96-20260520').reshape((96, 96)),
    'alpha36': get_arr('36-v2').reshape((36, 36)),
}

out_npz = 'assets/gemini_alpha_maps.npz'
np.savez_compressed(out_npz, **maps)
print('Saved NPZ size:', os.path.getsize(out_npz), 'bytes')
