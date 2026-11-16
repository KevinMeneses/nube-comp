"""Compara los renders de tests/out con lo que dice la teoría. Sale con código 1 si algo falla."""
import numpy as np, soundfile as sf, pathlib, sys
D = pathlib.Path(__file__).parent / "out"; S = pathlib.Path(__file__).parent / "signals"; SR = 48000
def a(db): return 10 ** (db / 20)
def db(x): return 20 * np.log10(np.abs(x) + 1e-15)
def load(name):
    x, sr = sf.read(D / f"{name}.wav"); assert sr == SR; return x
def lvl(name, t0=1.0, t1=1.9, ch=0):
    """nivel de pico de un seno (dBFS) a partir del RMS"""
    x = load(name)[int(t0 * SR):int(t1 * SR), ch]; return db(np.sqrt(np.mean(x ** 2)) * np.sqrt(2))
def env(x, ms=1.0):
    n = int(SR * ms / 1000); m = len(x) // n; return np.abs(x[:m * n]).reshape(m, n).max(1)
def harm(name, k):
    x = load(name)[SR:SR + 32768, 0] * np.hanning(32768); X = np.abs(np.fft.rfft(x)); f = np.fft.rfftfreq(32768, 1 / SR)
    pk = lambda fr: X[(f > fr - 30) & (f < fr + 30)].max()
    return db(pk(1000 * k) / pk(1000))

fails = 0
def scalar(name, got, want, tol):
    global fails
    ok = abs(got - want) <= tol
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:24s} {got:+8.2f}   (esperado {want:+.2f} ± {tol})")
def inrange(name, got, lo, hi):
    global fails
    ok = lo <= got <= hi
    fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:24s} {got:+8.2f}   (entre {lo:+.2f} y {hi:+.2f})")

def gr(L, T=-20, R=4, W=0):
    o = L - T; s = 0 if R >= 29.99 else 1 / R; s = 1 - s
    return 0 if 2 * o <= -W else s * (o + W / 2) ** 2 / (2 * W) if (W > 0 and 2 * o < W) else s * o

# NaN / explosiones en todo
for p in sorted(q for q in D.glob("*.wav") if not q.stem.startswith("perf_")):
    x = load(p.stem)
    if not np.all(np.isfinite(x)) or np.abs(x).max() > 4:
        fails += 1; print("MAL", p.stem, "tiene NaN o pasa de +12 dBFS")

x = load("below_null"); ref, _ = sf.read(S / "sine1k_m30.wav")
scalar("bajo umbral = intacto", db(np.abs(x - ref)[4800:-4800].max()), -140, 20)   # sin los fundidos del item
scalar("hard 4:1 (-6 → -16.5)", lvl("hard_r4"), -6 - gr(-6), 0.1)
scalar("rodilla 12 dB", lvl("soft_knee"), -6 - gr(-6, -10, 4, 12), 0.1)
scalar("ratio inf", lvl("r_inf"), -20, 0.1)
scalar("rango 3 dB", lvl("range3"), -9, 0.1)
scalar("ganancia +6", lvl("makeup6"), -16.5 + 6, 0.1)
scalar("auto ganancia", lvl("automk"), -16.5 + 0.5 * gr(0), 0.1)
scalar("mezcla 50 %", lvl("mix50"), db(0.5 * a(-6) * (1 + a(-gr(-6)))), 0.1)
scalar("detector RMS", lvl("rms_det"), -16.5, 0.3)
scalar("enlace 100 % L", lvl("link100", ch=0), -16.5, 0.1)
scalar("enlace 100 % R", lvl("link100", ch=1), -30 - gr(-6), 0.1)
scalar("enlace 0 % L", lvl("link0", ch=0), -16.5, 0.1)
scalar("enlace 0 % R", lvl("link0", ch=1), -30, 0.1)
gm = gr(db((a(-6) + a(-30)) / 2))
scalar("M/S L", lvl("ms_link", ch=0), -6 - gm, 0.1)
scalar("M/S R", lvl("ms_link", ch=1), -30 - gm, 0.1)
scalar("solo Mid (mono)", lvl("solo_mid"), -16.5, 0.1)
scalar("solo Side (mono) intacto", lvl("solo_side"), -6, 0.05)
inrange("sidechain ext: con SC", -10 - lvl("ext_sc", 0.4, 0.95), 3, 30)
scalar("sidechain ext: sin SC", lvl("ext_sc", 1.3, 1.9), -10, 0.1)
scalar("50 Hz sin filtro SC", lvl("lf_nohpf"), -16.5, 0.4)
scalar("50 Hz con corte SC 300", lvl("lf_hpf300"), -6, 0.1)
w = 50 / 300; scalar("escuchar SC (HPF 300)", lvl("sclisten"), -6 + db(w ** 2 / np.sqrt(1 + w ** 4)), 0.3)
scalar("enfoque +12 en 1k", lvl("focus"), -30 - gr(-18, -26), 0.3)
scalar("escuchar cambios", lvl("delta"), db(a(-6) * (1 - a(-gr(-6)))), 0.1)

# tiempos: GR por milisegundo = entrada / salida
ins, _ = sf.read(S / "step.wav")
def grcurve(name): return db(env(ins[:, 0]) / np.maximum(env(load(name)[:, 0]), 1e-9))
g = grcurve("timing")
print(f"    GR tras el escalón: " + " ".join(f"{t}ms:{g[1000 + t]:.1f}" for t in (1, 5, 10, 20, 40)))
inrange("ataque 10 ms (GR a 10 ms)", g[1010], 15 * (1 - np.exp(-1)) - 2, 15 * (1 - np.exp(-1)) + 2)
scalar("GR sostenida", g[1800], 15, 0.3)
print(f"    GR tras bajar:      " + " ".join(f"{t}ms:{g[2000 + t]:.1f}" for t in (10, 50, 100, 200, 400)))
inrange("release 100 ms (GR a 100 ms)", g[2100], 15 * np.exp(-1) - 1.5, 15 * np.exp(-1) + 1.5)
g = grcurve("hold")
inrange("hold 200: GR a 150 ms", g[2150], 13.5, 15.5)
inrange("hold 200: GR a 300 ms", g[2300], 15 * np.exp(-1) - 1.5, 15 * np.exp(-1) + 1.5)

# lookahead
for name in ("la_off", "la_5"):
    x = load(name)[:, 0]
    on = np.argmax(np.abs(x) > 1e-4)
    print(f"    {name}: arranca en la muestra {on} (debe ser ~48000)")
    if abs(on - 48000) > 3: fails += 1; print("MAL", name, "desalineado: la latencia no se compensó")
inrange("sin lookahead: pico 1er ms", db(np.abs(load("la_off")[48000:48048, 0]).max()), -9, 0)
inrange("lookahead 5 ms: pico 1er ms", db(np.abs(load("la_5")[48000:48048, 0]).max()), -60, -17)

# color
inrange("color 0: armónicos", max(harm("color0", 2), harm("color0", 3)), -200, -100)
h2, h3 = harm("color_fet", 2), harm("color_fet", 3)
print(f"    FET 50 %: H2 {h2:.1f} dB, H3 {h3:.1f} dB")
inrange("FET 50 %: H3", h3, -45, -20)
h2, h3 = harm("color_tubo", 2), harm("color_tubo", 3)
print(f"    Tubo 50 %: H2 {h2:.1f} dB, H3 {h3:.1f} dB")
inrange("Tubo 50 %: H2", h2, -40, -15)
if h2 <= h3: fails += 1; print("MAL Tubo: H2 debería dominar")

# estilos y presets: comprimen, no explotan
for st in range(5):
    g = grcurve(f"style{st}")
    if st == 0: scalar("estilo Limpio GR", g[1800], 15, 0.3)
    else: inrange(f"estilo {st} GR sostenida", g[1800], 5, 16)
    inrange(f"estilo {st} + auto/color GR", grcurve(f"style{st}_auto")[1800], 3, 17)
for p in range(1, 13):
    if p == 8:
        inrange("preset 8 (ducking) con SC", -10 - lvl("preset8", 0.4, 0.95), 3, 30)
    else:
        x = load(f"preset{p}")[:, 0]; inrange(f"preset {p}: nivel parte fuerte", db(np.sqrt(np.mean(x[int(1.5 * SR):int(1.9 * SR)] ** 2)) * np.sqrt(2)), -30, 0)
print("\nFALLAS:", fails)
sys.exit(1 if fails else 0)
