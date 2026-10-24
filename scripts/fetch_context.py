#!/usr/bin/env python3
"""
scripts/fetch_context.py - Root runner for immediate context extraction
"""
import sys
from pathlib import Path

# Redirect to the canonical skill script
skill_script = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "get-immediate-context" / "scripts" / "fetch_context.py"
if skill_script.is_file():
    with open(skill_script, "r", encoding="utf-8") as f:
        code = compile(f.read(), str(skill_script), "exec")
        exec(code)
else:
    print("[ERROR] Cannot find canonical script at:", skill_script)
