#!/usr/bin/env python3
"""Cek library PDF apa yang ADA di image produksi eduai-app."""
import subprocess

KODE = r"""
import importlib
for m in ['pypdf', 'PyPDF2', 'pdfminer', 'fitz', 'pdfplumber', 'zipfile',
          'docx', 'lxml']:
    try:
        importlib.import_module(m)
        print('ADA   :', m)
    except Exception:
        print('TIDAK :', m)
"""

r = subprocess.run(['docker', 'exec', 'eduai-app', 'python', '-c', KODE],
                   capture_output=True, text=True, timeout=60)
print(r.stdout or r.stderr[-800:])

r2 = subprocess.run(['cat', 'requirements.txt'], capture_output=True,
                    text=True, timeout=30)
print('══ requirements.txt ══')
print(r2.stdout)
