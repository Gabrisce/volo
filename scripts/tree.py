#!/usr/bin/env python3
import os

exclude = {".git", ".venv", "__pycache__", "node_modules"}
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in exclude]
    for f in files:
        print(os.path.relpath(os.path.join(root, f)))
