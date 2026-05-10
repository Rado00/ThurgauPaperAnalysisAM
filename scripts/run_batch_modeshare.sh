#!/usr/bin/env bash
# Lancia batch_run_modeshare.py da Git Bash su Windows.
# Attiva il virtualenv ThurgauAnalysisEnv e chiama lo script.
#
# Uso:
#   ./run_batch_modeshare.sh
#   ./run_batch_modeshare.sh --dry-run
#   ./run_batch_modeshare.sh --source "/c/Users/corra/OneDrive - ZHAW/.../altra_cartella"
#   ./run_batch_modeshare.sh --start-from 47
#
# Tutti gli argomenti vengono passati tali e quali a batch_run_modeshare.py.

set -e

VENV_ACTIVATE="/c/Users/corra/Documents/1_GitHub/PythonEnvironments/ThurgauAnalysisEnv/Scripts/activate"
SCRIPTS_DIR="/c/Users/corra/Documents/1_GitHub/ThurgauPaperAnalysisAM/scripts"

if [[ ! -f "$VENV_ACTIVATE" ]]; then
    echo "ERROR: virtualenv activate non trovato: $VENV_ACTIVATE"
    exit 1
fi

if [[ ! -d "$SCRIPTS_DIR" ]]; then
    echo "ERROR: scripts dir non trovata: $SCRIPTS_DIR"
    exit 1
fi

echo "Attivo virtualenv ThurgauAnalysisEnv..."
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"

echo "Python: $(which python)"
echo "Cartella scripts: $SCRIPTS_DIR"
echo

cd "$SCRIPTS_DIR"
python batch_run_modeshare.py "$@"
