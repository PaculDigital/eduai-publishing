#!/usr/bin/env python3
"""Probe 2: cari markup tab toolbar (btn-tab / tab home insert collab plugin)."""
import re

BASE = ('/var/www/onlyoffice/documentserver/web-apps/apps/'
        'documenteditor/main/')
for f in ('app/controller/Toolbar.js', 'app/view/Main.js'):
    try:
        t = open(BASE + f, encoding='utf-8', errors='ignore').read()
    except OSError:
        print(f, '— tidak ada'); continue
    print(f'\n═══ {f} ({len(t)} char) ═══')
    for pat, label in [
        (r'btn-tab-[a-z]+', 'btn-tab-*'),
        (r'id:\s*[\'"]tab-[a-z-]+[\'"]', 'id: tab-*'),
        (r'[\'"]tab-(home|insert|collab[a-z]*|plugin|layout|data|view|references|protect|ai)[a-z-]*[\'"]', 'nama tab'),
        (r'TabCollaboration|CollaborationTab', 'CollabTab'),
        (r'tabsmarkup|getTabsMarkup|fillTabs', 'markup fn'),
    ]:
        m = sorted(set(re.findall(pat, t)))[:10]
        if m:
            print(f'  {label}: {m}')
