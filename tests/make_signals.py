"""Señales de prueba (48 kHz, float32)."""
import numpy as np, soundfile as sf, pathlib
from scipy import signal as sg
D = pathlib.Path(__file__).parent / "signals"; D.mkdir(exist_ok=True)
SR = 48000
def a(db): return 10 ** (db / 20)
def save(name, *ch): sf.write(D / name, np.stack(ch, 1).astype(np.float32), SR, subtype="FLOAT")
n = SR * 2; t = np.arange(n) / SR
s = lambda f, db, tt=t: a(db) * np.sin(2 * np.pi * f * tt)
save("sine1k_m6.wav", s(1000, -6), s(1000, -6))
save("sine1k_m30.wav", s(1000, -30), s(1000, -30))
save("sine50_m6.wav", s(50, -6), s(50, -6))
save("lr.wav", s(1000, -6), s(1000, -30))
# escalon: -40 dBFS 0-1 s, -10 dBFS 1-2 s, -40 dBFS 2-3 s
t3 = np.arange(SR * 3) / SR
lv = np.where((t3 >= 1) & (t3 < 2), a(-10), a(-40))
st = lv * np.sin(2 * np.pi * 1000 * t3); save("step.wav", st, st)
# rafaga para el lookahead: silencio y 1 kHz a -6 dBFS desde 1.0 s (empieza en el pico)
b = np.zeros(n); i0 = SR; b[i0:] = a(-6) * np.cos(2 * np.pi * 1000 * (t[i0:] - 1.0)); save("burst.wav", b, b)
# sidechain: 1 kHz -10 dBFS en 1/2 siempre; ruido 300 Hz-4 kHz en 3/4 de 0.2 a 1.0 s
nz = np.random.default_rng(1).standard_normal(n); nz = sg.sosfilt(sg.butter(4, [300, 4000], "band", fs=SR, output="sos"), nz)
nz = 0.3 * nz / np.abs(nz).max(); nz[: int(0.2 * SR)] = 0; nz[int(1.0 * SR):] = 0
save("sidechain4.wav", s(1000, -10), s(1000, -10), nz, nz)
print("ok", sorted(p.name for p in D.iterdir()))
