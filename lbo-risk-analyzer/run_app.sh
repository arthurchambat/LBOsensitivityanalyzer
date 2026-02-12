#!/bin/bash
# Start the LBO Risk Analyzer app with correct library paths for PDF export

cd "$(dirname "$0")"
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
../.venv/bin/streamlit run app.py
