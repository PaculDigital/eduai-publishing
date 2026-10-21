#!/usr/bin/env python3
"""PERBAIKI peta/kerjakan: pakai `_revisi_kerja` (bukan ai_revisi endpoint).

BUG 3 (terukur 26Sep26): `ai_revisi()` = ENDPOINT (butuh Request sebagai
argumen pertama) → Wulan panggil `ai_revisi(body={...})` → TypeError →
HTTP 503. Yang benar: panggil INTI `_revisi_kerja(request, u, db)` dengan
Request buatan yang membawa body JSON.

CATATAN PAGAR: `_revisi_kerja` SENGAJA tidak memeriksa gerbang biaya
(dokumennya sendiri menyatakan begitu) — jadi Wulan TETAP memotong token
sendiri SEBELUM memanggil (jangan dobel, jangan nol).
"""
import pathlib

AI = pathlib.Path('/opt/data/services/eduai-publishing/app/ai.py')
s = AI.read_text()

LAMA = """        hasil_kerja: dict[str, Any] = {}
        try:
            hasil_kerja = await ai_revisi(
                body={'file_id': body.get('file_id'),
                      'permintaan': perintah,
                      'intent': 'perkaya'},
                db=db, u=u)
        except Exception as e:"""

BARU = """        hasil_kerja: dict[str, Any] = {}
        try:
            #  ⚠️ `ai_revisi()` adalah ENDPOINT (argumen pertama = Request)
            #     dan gerbang biayanya sudah diperiksa DI ATAS (token sudah
            #     dipotong). Jadi yang dipanggil = INTI `_revisi_kerja()`
            #     dengan Request tiruan yang membawa body JSON.
            from starlette.requests import Request as _Req

            _body = json.dumps({
                'file_id': body.get('file_id'),
                'permintaan': perintah,
                'komentar': [{'isi': perintah, 'jenis': 'perkaya'}],
            }).encode()

            async def _terima():
                return {'type': 'http.request', 'body': _body, 'more_body': False}

            _req = _Req({'type': 'http', 'method': 'POST', 'path': '/',
                         'headers': [(b'content-type', b'application/json')]})
            _req._receive = _terima                        # noqa: SLF001
            hasil_kerja = await _revisi_kerja(_req, u, db)
        except Exception as e:"""

if LAMA not in s:
    print('❌ pola tidak ditemukan — cek ulang kode')
    raise SystemExit(1)
s = s.replace(LAMA, BARU, 1)
AI.write_text(s)

import ast
ast.parse(s)
print('✅ peta/kerjakan sekarang memakai _revisi_kerja (inti)')
print(f'   baris: {len(s.splitlines())}')
