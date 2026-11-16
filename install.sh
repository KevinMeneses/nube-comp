#!/bin/zsh
# Instala Nube Comp en REAPER (macOS) como enlace: los cambios del repo se ven al volver a insertar el FX.
set -e
DST="$HOME/Library/Application Support/REAPER/Effects/Nube Comp"
cd "$(dirname "$0")"
mkdir -p "$DST"
ln -sf "$PWD/nube_comp.jsfx" "$DST/nube_comp.jsfx"
echo "Listo: en REAPER busca \"Nube Comp\" en el navegador de FX (JS: Nube Comp)."
