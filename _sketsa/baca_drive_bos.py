#!/usr/bin/env python3
"""BACA folder Google Drive publik (05Okt26) — pakai Chrome CDP :9333.

Alat potret: _sketsa/potret_cdp.py (sudah ada; Tab.cmd / tab_baru).
Daftar berkas Drive publik tersimpan di window['_DRIVE_ivd'] (JSON string).
"""
from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import Tab, tab_baru, bersihkan_tab       # noqa: E402

URL = ('https://drive.google.com/drive/folders/'
       '1wVAiT3nhZO0m8HoGl3FcfgyPPtQRqNlz?usp=sharing')


def ev(tab: Tab, ekspresi: str):
    r = tab.cmd('Runtime.evaluate',
                {'expression': ekspresi, 'returnByValue': True,
                 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value')


bersihkan_tab()
tab, tid = tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Page.navigate', {'url': URL})
    time.sleep(9)

    print('judul :', ev(tab, 'document.title'))
    print('url   :', ev(tab, 'location.href'))
    print()

    ada = ev(tab, "typeof window['_DRIVE_ivd']")
    print("_DRIVE_ivd:", ada)

    if ada not in (None, 'undefined'):
        data = ev(tab, """(function(){
            var s = window['_DRIVE_ivd'];
            if (typeof s !== 'string') { try { s = JSON.stringify(s); } catch(e){ return null; } }
            return s;
        })()""")
        if data:
            try:
                j = json.loads(data.replace('\\"', '"'))
            except Exception:
                try:
                    j = json.loads(data.encode().decode('unicode_escape'))
                except Exception as e:                         # noqa: BLE001
                    print('gagal urai:', e)
                    j = None
            if j:
                isi = j[0] if isinstance(j, list) and j else j
                print(f'  jumlah baris: {len(isi) if hasattr(isi, "__len__") else "?"}')
                for baris in (isi if isinstance(isi, list) else []):
                    if isinstance(baris, list) and len(baris) >= 3:
                        fid = baris[0]
                        nama = baris[2] if isinstance(baris[2], str) else str(baris[2])
                        print(f'    {fid}  {nama[:70]}')
    else:
        print('(cadangan) DOM:')
        print(ev(tab, """(function(){
            var out=[];
            document.querySelectorAll('[data-id]').forEach(function(e){
                var t=(e.getAttribute('aria-label')||e.textContent||'').trim().slice(0,80);
                if(t) out.push(e.getAttribute('data-id')+' | '+t);
            });
            return out.slice(0,40).join('\\n');
        })()"""))
finally:
    tab.tutup()
