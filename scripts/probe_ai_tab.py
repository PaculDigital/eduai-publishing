#!/usr/bin/env python3
"""Probe: syarat tab AI muncul di Toolbar.js + sumber usedPlugins."""
import re

T = '/var/www/onlyoffice/documentserver/web-apps/apps/documenteditor/main/app/controller/Toolbar.js'
t = open(T, encoding='utf-8', errors='ignore').read()

# 1. konteks 9DC93CDB
for m in re.finditer(r'9DC93CDB', t):
    i = m.start()
    print('=== 9DC93CDB @', i, '===')
    print(t[max(0, i-1500):i+600])
    print()

# 2. usedPlugins di Plugins.js
P = '/var/www/onlyoffice/documentserver/web-apps/apps/common/main/lib/controller/Plugins.js'
p = open(P, encoding='utf-8', errors='ignore').read()
for m in re.finditer(r'usedPlugins', p):
    i = m.start()
    print('=== usedPlugins @', i, '===')
    print(t2 := p[max(0, i-600):i+300])
    print()
    break

# 3. autostart di mana saja (web-apps)
import subprocess
