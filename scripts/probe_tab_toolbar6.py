#!/usr/bin/env python3
"""Probe 6: Mixtbar.js = komponen toolbar OO — cara render tab & DOM-nya."""
import re

f = ('/var/www/onlyoffice/documentserver/web-apps/apps/common/main/'
     'lib/component/Mixtbar.js')
t = open(f, encoding='utf-8', errors='ignore').read()
print('panjang:', len(t))

i = t.find('addTab: function')
if i == -1:
    i = t.find('addTab(')
print('═══ addTab ═══')
print(t[i:i + 1500])
