#!/bin/bash
# Run all backend tests
set -e
cd "$(dirname "$0")/backend"
python -m pytest tests/ -v "$@"
