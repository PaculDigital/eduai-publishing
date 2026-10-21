#!/usr/bin/env python3
"""UJI JEV SUNGGUHAN atas naskah ASIH — panggil 9router betulan.

WAJIB dari DALAM container (butuh jaringan 9router):
    docker cp _uji_jev_sungguhan.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _uji_jev_sungguhan.py

Mengukur: WAKTU + MODEL ASLI + jawaban Jev (jumlah bab, daftar bab, bagian
wajib artikel, sub-bab) — supaya bisa dibandingkan dengan peta mesin.

ATURAN LAPORAN BOS: laporan WAJIB menyebut waktu + nama model asli + panjang
prompt. Skrip ini mencetak ketiganya. Kalau Jev tidak bisa dihubungi →
laporkan APA ADANYA, jangan tarik klaim.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')

NASKAH_ASIH = Path('/app/uploads/8/3dbd8babe72c6098.docx')
BASE = (os.getenv('EDUAI_SATPAM_BASE')
        or 'http://9router:20128/v1/chat/completions').strip()
MODEL = (os.getenv('EDUAI_SATPAM_MODEL') or 'SATPAM/typesafe/jev-1.13').strip()
KUNCI = (os.getenv('EDUAI_SATPAM_KEY') or os.getenv('EDUAI_ROUTER_KEY') or '').strip()


def teks_docx(jalur: Path) -> str:
    with zipfile.ZipFile(jalur) as z:
        x = z.read('word/document.xml').decode('utf-8', 'ignore')
    t = x.replace('</w:p>', '\n')
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'[ \t]{2,}', ' ', t)


def main() -> int:
    print('══ UJI JEV SUNGGUHAN — NASKAH ASIH ══')
    if not NASKAH_ASIH.is_file():
        print(f'❌ naskah tidak ada: {NASKAH_ASIH}')
        return 2

    naskah = teks_docx(NASKAH_ASIH)
    print(f'naskah    : {NASKAH_ASIH.name} ({len(naskah):,} kar)')
    print(f'BASE      : {BASE}')
    print(f'MODEL     : {MODEL}')
    print(f'KUNCI ada : {bool(KUNCI)}')

    #  bahan Jev — pakai penyusun bahan ASLI milik app (jangan bikin baru)
    from app import satpam
    from app.state import petakan
    peta_mesin = petakan(naskah) or []
    isi = satpam._susun_state(naskah, peta_mesin)
    print(f'peta mesin: {len(peta_mesin)} bagian')
    print(f'bahan Jev : {len(isi):,} karakter')

    from app.konversi import PERTANYAAN_PETA
    pertanyaan = PERTANYAAN_PETA          # 3 pertanyaan TETAP (skema Jev tertutup)
    print(f'pertanyaan: {list(pertanyaan.keys())}')

    body = {'model': MODEL,
            'messages': [{'role': 'user',
                          'content': json.dumps({'state': isi,
                                                 'questions': pertanyaan})}]}
    panjang_prompt = len(json.dumps(body))
    print(f'prompt    : {panjang_prompt:,} karakter')

    req = urllib.request.Request(
        BASE, data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {KUNCI}',
                 'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            mentah = r.read().decode()
        dtk = time.time() - t0
    except Exception as e:                                    # noqa: BLE001
        dtk = time.time() - t0
        print(f'\n❌ JEV TIDAK BISA DIHUBUNGI setelah {dtk:.1f} dtk: '
              f'{type(e).__name__}: {e}')
        return 1

    print(f'\n✅ Jev MENJAWAB dalam {dtk:.1f} detik ({len(mentah):,} byte)')
    print(f'MODEL ASLI: {MODEL}')
    print(f'WAKTU     : {dtk:.1f} detik')
    print(f'PROMPT    : {panjang_prompt:,} karakter')

    jawab = satpam._urai_balasan(mentah)
    print(f'\n--- JAWABAN JEV (urai) ---')
    if jawab is None:
        print('(tidak terbaca sebagai JSON)')
        print(mentah[:1500])
        return 1

    for nama, isi_j in jawab.items():
        print(f'  {nama}: {json.dumps(isi_j, ensure_ascii=False)[:300]}')

    #  bandingkan jumlah bab Jev vs mesin
    jml = (jawab.get('jumlah_bab') or {}).get('choice')
    conf = (jawab.get('jumlah_bab') or {}).get('confidence')
    print(f'\n--- PEMBANDINGAN ---')
    print(f'Jev hitung bab : {jml} (keyakinan {conf})')
    print(f'Mesin temukan  : {len(peta_mesin)} bagian')
    kat = sorted({str(p.get('kategori') or '') for p in peta_mesin
                  if isinstance(p, dict)})
    print(f'kategori mesin : {kat}')

    #  jawaban "bagian wajib" — cek Jev melihat metode/hasil/kesimpulan
    wajib = str((jawab.get('bagian_wajib_artikel') or {}).get('text') or '')
    print(f'bagian wajib (Jev): {wajib[:200]}')

    #  tulis hasil ke berkas untuk bukti
    Path('/tmp/jev_sungguhan.json').write_text(
        json.dumps({'model': MODEL, 'detik': round(dtk, 1),
                    'prompt_kar': panjang_prompt, 'jawaban': jawab},
                   ensure_ascii=False, indent=2))
    print('\n(bukti disimpan: /tmp/jev_sungguhan.json)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
