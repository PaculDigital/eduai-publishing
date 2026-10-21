"""Apakah blok {% for bk in berkas %} benar-benar JALAN di rute asli?

Cetak: berapa berkas yang diterima template, dan isi syaratnya.
Dilakukan dengan monkeypatch ringan pada TemplateResponse? Tidak —
lebih jujur: panggil rute lewat TestClient sambil MENCATAT konteks.
Kita bungkus _tpl.TemplateResponse supaya konteksnya kelihatan.
"""
import sys

sys.path.insert(0, '/app')

from fastapi.testclient import TestClient  # noqa: E402

import app.rute_pembimbing as RP  # noqa: E402
from app.main import app  # noqa: E402

TOKEN = 'GDvcGFpt212WDANwJcaym_YkRx2byUl4cu-EJCwQkus'

asli = RP._tpl.TemplateResponse


def intip(*a, **kw):
    #  TemplateResponse(name, context) ATAU (name, request, context)?
    nama = a[0] if a else kw.get('name')
    konteks = None
    for x in a:
        if isinstance(x, dict):
            konteks = x
    if konteks is None and 'context' in kw:
        konteks = kw['context']
    print('>>> TemplateResponse dipanggil:', nama)
    if konteks:
        print('    kunci konteks:', sorted(konteks.keys())[:20])
        bk = konteks.get('berkas')
        print('    berkas:', type(bk).__name__, '| jumlah =',
              len(bk) if bk is not None else 'None')
        if bk:
            for x in bk:
                print('       → id=', getattr(x, 'id', '?'),
                      '| file_id=', repr(getattr(x, 'file_id', '?')))
        print('    ai_aktif =', repr(konteks.get('ai_aktif')))
    return asli(*a, **kw)


RP._tpl.TemplateResponse = intip

with TestClient(app) as c:
    r = c.get(f'/tinjau/{TOKEN}', follow_redirects=False)
    print()
    print('HTTP:', r.status_code, '| ukuran:', len(r.text))
