#!/usr/bin/env python3
"""Probe 4: cari definisi addTab -> bagaimana DOM tab dibangun."""
import glob
import re

pola = []
for f in glob.glob('/var/www/onlyoffice/documentserver/web-apps/apps/**/view/Toolbar*.js',
                   recursive=True):
    t = open(f, encoding='utf-8', errors='ignore').read()
    if 'addTab' in t:
        pola.append(f)
        i = t.find('addTab: function')
        if i == -1:
            i = t.find('addTab(')
        print('═══', f, '═══')
        print(t[max(0, i - 100):i + 1200])
        break
if not pola:
    print('addTab tidak ketemu di view/Toolbar*.js')
