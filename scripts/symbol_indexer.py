#!/usr/bin/env python3
"""
scripts/symbol_indexer.py - Root runner for live symbol and line indexing
"""
import sys
from pathlib import Path

skill_script = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "get-immediate-context" / "scripts" / "symbol_indexer.py"
if skill_script.is_file():
    with open(skill_script, "r", encoding="utf-8") as f:
        code = compile(f.read(), str(skill_script), "exec")
        exec(code)
else:
    print("[ERROR] Cannot find canonical script at:", skill_script)
