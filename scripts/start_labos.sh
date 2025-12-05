#!/usr/bin/env bash
set -e

# Move to repo root relative to this script
cd "$(dirname "$0")/.."

echo "Launching LabOS from: $(pwd)"
echo

# TODO: Adjust command if you use a different server runtime
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
