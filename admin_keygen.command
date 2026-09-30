#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -f "./venv/bin/python" ]; then
    ./venv/bin/python admin_keygen.py "$@"
elif command -v python3 &>/dev/null; then
    python3 admin_keygen.py "$@"
else
    python admin_keygen.py "$@"
fi
