#!/usr/bin/env python3
"""Probe 3: konteks TabCollaboration di controller/Toolbar.js — bagaimana
tab dibuat (id elemen? class?) supaya pewarnaan CSS bisa menargetnya."""
import re

BASE = ('/var/www/onlyoffice/documentserver/web-apps/apps/'
        'documenteditor/main/app/controller/Toolbar.js')
t = open(BASE, encoding='utf-8', errors='ignore').read()

i = t.find('TabCollaboration')
while i != -1 and i < len(t):
    print('═══ konteks @', i, '═══')
    print(t[max(0, i - 400):i + 700])
    print()
    ni = t.find('TabCollaboration', i + 1)
    if ni == -1 or ni > i + 5000:
        break
    i = ni
    if i > 60000:
        break
