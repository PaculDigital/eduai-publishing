#!/usr/bin/env python3
"""Probe struktur TAB TOOLBAR OnlyOffice — cari selector CSS untuk tab
Kolaborasi & tab AI. Dijalankan DI DALAM container oo-converter.

Cetak: id/class elemen tab toolbar + CSS class bawaan, supaya bisa
diputuskan apakah pewarnaan via CSS murni aman (tanpa ubah JS core).
"""
import re

BASE = ('/var/www/onlyoffice/documentserver/web-apps/apps/'
        'documenteditor/main/app/view/Toolbar.js')
t = open(BASE, encoding='utf-8', errors='ignore').read()

print('panjang file:', len(t), 'char')

# 1) semua id yang mengandung 'tab'
ids = sorted(set(re.findall(r'id:\s*[\'"]([a-z0-9_-]{2,40})[\'"]', t)))
tabs = [i for i in ids if 'tab' in i]
print('\n== id mengandung "tab" ==')
print(tabs[:25])

# 2) nama tab kategori (home/insert/collab/plugin)
cats = sorted(set(re.findall(r'[\'"]([A-Za-z]+Tab[\'"]?)', t)))
print('\n== pola XxTab ==')
print(cats[:25])

# 3) id tombol kategori toolbar OO klasik: 'tlbtn-...' / 'btn-category'
cats2 = sorted(set(re.findall(r'[\'"]((?:tlbtn|btn)-[a-z0-9-]+)[\'"]', t)))
print('\n== tlbtn-/btn- ==')
print(cats2[:25])

# 4) cari referensi 'Collaboration' sbg judul tab di view
col = re.findall(r'[\'"]([^\'"]{0,30}[Cc]ollaboration[^\'"]{0,10})[\'"]', t)
print('\n== Collaboration ==')
print(sorted(set(col))[:10])

# 5) class 'toolbar' custom OO: 'box-tab' dll
cls = sorted(set(re.findall(r'cls:\s*[\'"]([^\'"]{2,50})[\'"]', t)))
print('\n== cls: ==')
print([c for c in cls if 'tab' in c.lower() or 'categor' in c.lower()][:15])
