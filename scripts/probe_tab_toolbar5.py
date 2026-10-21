#!/usr/bin/env python3
"""Probe 5: grep addTab di SELURUH web-apps (view mana pun)."""
import glob

hasil = []
for f in glob.glob('/var/www/onlyoffice/documentserver/web-apps/apps/**/*.js',
                   recursive=True):
    if '.gz' in f or 'node_modules' in f:
        continue
    try:
        t = open(f, encoding='utf-8', errors='ignore').read()
    except OSError:
        continue
    if 'addTab: function' in t or 'addTab = function' in t or 'addTab(' in t:
        hasil.append(f)
print('\n'.join(hasil[:12]))
print('total:', len(hasil))
