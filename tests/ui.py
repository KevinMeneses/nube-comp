"""Ayudante para probar la interfaz con cliclick (ventana del FX en su posición/tamaño por defecto)."""
import subprocess, time, pathlib
WX, WY = 26, 66 + 53            # esquina del área gráfica del FX (puntos), bajo la cabecera de REAPER
ROOT = pathlib.Path(__file__).resolve().parent.parent
def pt(x, y): return f"{round(WX + x)},{round(WY + y)}"
def cc(*args): subprocess.run(["cliclick", "-w", "60", *args], check=True); time.sleep(0.4)
def wheel(n): subprocess.run(["swift", str(ROOT / "tests/scroll.swift"), str(n)], check=True); time.sleep(0.4)
def shot(path): subprocess.run(["screencapture", "-x", "-R26,66,1000,693", path], check=True); return path
def dump():
    p = ROOT / "tests/out/dump.txt"; p.unlink(missing_ok=True)
    subprocess.Popen(["/Applications/REAPER.app/Contents/MacOS/REAPER", "-nonewinst", str(ROOT / "tests/ui_dump.lua")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if p.exists() and "done" in p.read_text(): return p.read_text().replace("done\n", "")
        time.sleep(0.25)
    return "(sin respuesta)"
# layout (ventana 1000x640): py = 386
PY = 386
STYLE = lambda k: (14 + 56 + k * 90 + 43, PY + 6 + 14)
KNOB = lambda i: (56 + i * 86, PY + 92)
SMALL = lambda i: (46 + i * 72, PY + 184)
