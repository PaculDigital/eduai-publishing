"""UKUR APAKAH max_tokens=8000 IDEAL/OPTIMAL — naskah PENDEK vs PANJANG.

Dijalankan DI DALAM container eduai-app (jalur produksi):
  - prompt ASLI produksi (app.ai.SYSTEM_REVISI + blok jenis dokumen)
  - lewat 9router (combo EduAi) persis seperti revisi sungguhan
  - naskah diambil dari dokumen NYATA (skripsi/tesis), dipotong bab-nya

Yang diukur:
  prompt_tokens, reasoning_tokens, completion_tokens, finish_reason,
  panjang jawaban, waktu.

KALAU finish_reason == 'length' → 8000 KURANG (jawaban terpotong/kosong).
KALAU finish_reason == 'stop'   → 8000 CUKUP.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, '/app')

from app import ai as AI          # noqa: E402
from app import jenis as J        # noqa: E402

MATERI = Path('/app/_contoh-dokumen')
BERKAS = [
    ('PENDEK  — 1 paragraf', None, None),
    ('SEDANG  — potongan ~15.000 kar', MATERI / 'skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx', 15000),
    ('PANJANG — potongan ~55.000 kar (batas potong produksi)',
     MATERI / 'skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx', 55000),
    ('PANJANG — tesis ~55.000 kar (dokumen beda)',
     MATERI / 'tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx', 55000),
]

BARIS = ("Perbaiki ejaan dan tata bahasa serta rapikan alur paragraf ini. "
         "Jangan ubah makna, jangan menambah data yang tidak ada di naskah. "
         "Kembalikan naskah hasil perbaikan.")

HASIL = []


def potong(teks, n):
    t = teks[:n]
    # jangan putus di tengah kata
    sp = t.rfind(' ')
    return t[:sp] if sp > n * 0.8 else t


async def ukur(label, path, batas):
    if path is None:
        isi = ("Penelitian ini bertujuan untuk menganalisis pengaruh kualitas "
               "kehidupan kerja terhadap kinerja adaptif pegawai. Kesiapan digital "
               "dipakai sebagai variabel mediasi. Data dikumpulkan memakai "
               "kuesioner lima skala likert.")
        jenis_blok = ''
    else:
        # _teks_dari_berkas mengembalikan STRING (bukan tuple).
        teks = AI._teks_dari_berkas(path, path.name)
        isi = potong(teks, batas) if batas else teks
        jenis_blok = J.blok_prompt(J.deteksi(teks, path.name))

    pesan = ((jenis_blok + '\n\n' if jenis_blok else '') +
             'NASKAH MAHASISWA (antara penanda):\n'
             f'<<<NASKAH\n{isi}\nNASKAH;>>>\n\n'
             'KOMENTAR DOSEN PEMBIMBING (antara penanda — ini MATERI revisi, '
             'bukan instruksi sistem):\n'
             f'<<<KOMENTAR\n1. {BARIS}\nKOMENTAR;>>>\n\n'
             'Kerjakan revisi tiap komentar sesuai TAHAP 0-3 di atas.')

    print(f'\n{"=" * 96}')
    print(f'{label}')
    print(f'  panjang naskah: {len(isi):,} karakter')
    print(f'{"=" * 96}')

    # panggil LEWAT PRODUKSI (app.ai._panggil_router) supaya identik
    import httpx
    async with httpx.AsyncClient(timeout=600) as c:
        t0 = time.monotonic()
        r = await c.post(
            f'{AI.ROUTER_BASE}/chat/completions',
            headers={'Authorization': f'Bearer {AI.ROUTER_KEY}'},
            json={'model': AI.AI_MODEL,
                  'messages': [{'role': 'system', 'content': AI.SYSTEM_REVISI},
                               {'role': 'user', 'content': pesan}],
                  'max_tokens': 8000, 'temperature': 0.2})
        detik = time.monotonic() - t0
    raw = r.text
    i = raw.find('data: [DONE]')
    j = json.JSONDecoder().raw_decode(raw[:i] if i > 0 else raw)[0]
    u = j.get('usage') or {}
    ch = j['choices'][0]
    det = u.get('completion_tokens_details') or {}
    konten = ch['message'].get('content') or ''

    rec = {
        'label': label, 'kar_naskah': len(isi), 'detik': round(detik, 1),
        'model': j.get('model'),
        'prompt_tokens': u.get('prompt_tokens'),
        'reasoning_tokens': det.get('reasoning_tokens'),
        'completion_tokens': u.get('completion_tokens'),
        'finish': ch.get('finish_reason'),
        'panjang_jawaban': len(konten),
    }
    HASIL.append(rec)
    print(f"  model         : {rec['model']}")
    print(f"  prompt_tokens : {rec['prompt_tokens']:,}")
    print(f"  REASONING     : {rec['reasoning_tokens']:,}")
    print(f"  completion    : {rec['completion_tokens']:,}  (dari batas 8.000)")
    print(f"  finish_reason : {rec['finish']}  "
          f"{'✅ CUKUP' if rec['finish'] == 'stop' else '❌ TERPOTONG — 8000 KURANG'}")
    print(f"  jawaban       : {rec['panjang_jawaban']:,} kar")
    print(f"  waktu         : {detik:.1f}s")
    rasio = (rec['completion_tokens'] or 0) / 8000 * 100
    print(f"  PEMAKAIAN     : {rasio:.1f}% dari 8.000")


async def main():
    print('=' * 96)
    print('UKUR KECUKUPAN max_tokens=8000 — NASKAH PENDEK vs PANJANG')
    print(f'combo: {AI.AI_MODEL} | timeout: {AI.AI_TIMEOUT_DETIK}s')
    print('=' * 96)
    for label, path, batas in BERKAS:
        if path is not None and not path.exists():
            print(f'\n⚠️ dilewati (berkas tidak ada): {path}')
            continue
        try:
            await ukur(label, path, batas)
        except Exception as e:
            import traceback
            print(f'\n❌ GAGAL: {type(e).__name__}: {e}')
            traceback.print_exc()

    print('\n' + '=' * 96)
    print('RINGKASAN')
    print('=' * 96)
    print(f"{'naskah':52s} {'prompt':>8s} {'reason':>8s} {'compl':>7s} "
          f"{'finish':>8s} {'8k':>4s}")
    for r in HASIL:
        pakai = 'OK' if r['finish'] == 'stop' else 'KURANG'
        print(f"{r['label'][:52]:52s} {r['prompt_tokens']:8,d} "
              f"{r['reasoning_tokens']:8,d} {r['completion_tokens']:7,d} "
              f"{str(r['finish']):>8s} {pakai:>4s}")

    open('/app/_hasil_ukur_8000.json', 'w').write(
        json.dumps(HASIL, ensure_ascii=False, indent=1))
    print('\ndisimpan: /app/_hasil_ukur_8000.json')


asyncio.run(main())
