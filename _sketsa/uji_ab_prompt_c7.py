"""UJI A/B SYSTEM PROMPT — Opsi 1, 28Sep26. LAMA (pre-Opsi1) vs BARU.

Pertanyaan: apakah dua suntingan Opsi 1 (PANJANG PRESISI + NYAMBUNG +
"SATU BLOK PER PARAGRAF") yang membuat AI menjawab "TIDAK ADA PERUBAHAN"
pada uji jalur nyata tadi — atau memang naskah/modelnya?

FAKTA struktur (diukur 28Sep26): aturan G1–G7e ada di SYSTEM prompt
(`ai.SYSTEM_REVISI`, di-strip dari prompts/revisi_produksi.txt), BUKAN di
user message. Jadi A/B = tukar `ai.SYSTEM_REVISI`; user message (naskah +
komentar) TETAP SAMA SEMPURNA di kedua varian.

2 ARAH: tiap varian dipanggilkan ke model/yg sama, hasil dilewatkan
pipeline asli (`_revisi_kerja` → `pipa.periksa`) — bukan penilaian manual.

Jalankan di dalam container dengan PYTHONPATH=/app.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, '/app')
import app.ai as ai                          # noqa: E402
from app.ai import _RequestTiruan, _revisi_kerja   # noqa: E402
from app.models import SessionLocal, User    # noqa: E402

FILE_ID = 65
KOMENTAR = ['Latar belakang terlalu pendek dan kurang jelas. '
            'Perdalam dengan teori dan data terbaru.']
EMAIL = 'uji-berbayar-e2e@test.local'

SYSTEM_BARU = ai.SYSTEM_REVISI
SYSTEM_LAMA = ai._strip_komentar_header(Path('/tmp/prompt_lama.txt').read_text())
assert 'PANJANG PRESISI' in SYSTEM_BARU, 'system BARU tidak berisi aturan baru'
assert 'PANJANG PRESISI' not in SYSTEM_LAMA, 'system LAMA masih berisi aturan baru'
print(f'== SYSTEM: BARU={len(SYSTEM_BARU)} kar · LAMA={len(SYSTEM_LAMA)} kar '
      f'(selisih {len(SYSTEM_BARU) - len(SYSTEM_LAMA)} kar) ==', flush=True)

# ── rebut prompt (tanpa panggil AI) untuk memastikan user_msg SAMA ──────
class _Berhenti(Exception):
    pass


async def _tangkap(user_msg, timeout, system=None, gambar=None):
    _tangkap.user = user_msg or ''
    raise _Berhenti()


ai._panggil_router = _tangkap


async def _jalan(varian):
    """Satu putaran: set system sesuai varian, panggil model terkendali."""
    ai.SYSTEM_REVISI = SYSTEM_LAMA if varian == 'LAMA' else SYSTEM_BARU

    async def _paksa(user_msg, timeout, system=None, gambar=None, **sisa):
        if JALUR == 'jalur1':
            konten, info = await ai._panggil_9router(
                user_msg, timeout, system=system, gambar=gambar)
        else:
            asli = ai.daftar_fallback
            ai.daftar_fallback = lambda: [(MODEL, '')]
            try:
                konten, info = await ai._panggil_openrouter(
                    user_msg, timeout, system=system)
            finally:
                ai.daftar_fallback = asli
        MENTAH['isi'] = konten
        MENTAH['info'] = dict(info or {})
        #  simpan MENTAH sekarang juga — kalau pipeline menolak, jawaban
        #  AI tetap bisa diperiksa (cacat uji 28Sep: output hilang saat 503).
        try:
            with open(f'/app/data/_ab_raw_{varian}_{model}.txt', 'a') as f:
                f.write(f'\n\n===== varian={varian} model={model} '
                        f'system_kar={len(ai.SYSTEM_REVISI)} '
                        f'out={len(konten)} info={info} =====\n')
                f.write(konten)
        except Exception as _e:                          # noqa: BLE001
            print(f'  (simpan raw gagal: {_e})', flush=True)
        return konten, info

    ai._panggil_router = _paksa
    db = SessionLocal()
    u = db.query(User).filter(User.email == EMAIL).first()
    assert u, 'user uji tidak ada'
    hasil = await _revisi_kerja(
        _RequestTiruan({'file_id': FILE_ID, 'komentar': KOMENTAR}), u, db)
    db.close()
    return hasil


JALUR, MODEL = 'jalur2', ''
MENTAH = {'isi': '', 'info': {}}

# rebut user message dulu (bukti: pesan yang sama dipakai kedua varian)
_db0 = SessionLocal()
_u0 = _db0.query(User).filter(User.email == EMAIL).first()
assert _u0, 'user uji tidak ada'
try:
    asyncio.run(_revisi_kerja(
        _RequestTiruan({'file_id': FILE_ID, 'komentar': KOMENTAR}), _u0, _db0))
except _Berhenti:
    pass
except Exception:                                             # noqa: BLE001
    pass
user_asal = getattr(_tangkap, 'user', '')
print(f'== user message asli: {len(user_asal)} kar ==', flush=True)

EKSPERIMEN = [
    ('LAMA', 'glm-5.3-flash', 'jalur2'),
    ('BARU', 'glm-5.3-flash', 'jalur2'),
    ('LAMA', 'deepseek-v4.1-flash', 'jalur2'),
    ('BARU', 'deepseek-v4.1-flash', 'jalur2'),
    ('LAMA', 'EduAi', 'jalur1'),
    ('BARU', 'EduAi', 'jalur1'),
]

#  UJI ASAP (28Sep26): AB_MODEL=deepseek → jalankan sebagian dulu supaya
#  perpipaan (system bertukar, model dipaksa, hasil dipipeline) terbukti
#  sebelum 6 putaran penuh menghabiskan waktu & saldo.
_filter = os.environ.get('AB_MODEL', '')
if _filter:
    EKSPERIMEN = [e for e in EKSPERIMEN if _filter in e[1]]
    print(f'== filter AB_MODEL={_filter!r} → {len(EKSPERIMEN)} putaran ==',
          flush=True)

HASIL = []
for varian, model, jalur in EKSPERIMEN:
    JALUR, MODEL = jalur, model
    MENTAH.update({'isi': '', 'info': {}})
    t0 = time.monotonic()
    print(f'-->> {varian} @ {model} ({jalur})', flush=True)
    try:
        hasil = asyncio.run(_jalan(varian))
        dtk = time.monotonic() - t0
        isi = MENTAH['isi']
        ada_tidak = 'TIDAK ADA PERUBAHAN' in isi
        if isinstance(hasil, dict):
            n_edit = len(hasil.get('editan') or [])
            ditolak = hasil.get('ditolak') or []
            kunci = {k: str(hasil.get(k))[:220] for k in
                     ('ok', 'pesan', 'intent', 'jumlah_editan')
                     if k in hasil}
            if not kunci:
                kunci = {k: str(v)[:220] for k, v in hasil.items()}
        else:
            n_edit, ditolak, kunci = 0, [], {'hasil': repr(hasil)[:220]}
        print(f'    {dtk:.1f} dtk · out={len(isi)} kar · editan={n_edit} · '
              f'TIDAK_ADA_PERUBAHAN={ada_tidak} · '
              f'ditolak={[(d.get("sebab"), d.get("rasio_paragraf"))
                          for d in ditolak]}', flush=True)
        print(f'    kunci={kunci}', flush=True)
        HASIL.append({'varian': varian, 'model': model, 'jalur': jalur,
                      'dtk': round(dtk, 1), 'out_kar': len(isi),
                      'editan': n_edit, 'tidak_ada': ada_tidak,
                      'ditolak': [d.get('sebab') for d in ditolak],
                      'kunci': kunci,
                      'info': {k: str(v)[:120] for k, v in
                               MENTAH['info'].items()},
                      'potongan_awal': isi[:700],
                      'potongan_akhir': isi[-700:]})
    except Exception as e:                                   # noqa: BLE001
        dtk = time.monotonic() - t0
        pesan = str(e)[:500]
        isi = MENTAH['isi']
        print(f'    GALAT {dtk:.1f} dtk · {type(e).__name__}: {pesan}', flush=True)
        print(f'    (jawaban mentah out={len(isi)} kar · '
              f'TIDAK_ADA_PERUBAHAN={"TIDAK ADA PERUBAHAN" in isi} · '
              f'awal={isi[:160]!r})', flush=True)
        HASIL.append({'varian': varian, 'model': model, 'jalur': jalur,
                      'dtk': round(dtk, 1), 'out_kar': len(isi),
                      'galat': f'{type(e).__name__}: {pesan}',
                      'potongan_awal': isi[:700],
                      'potongan_akhir': isi[-700:]})
    time.sleep(3)

print('\n== RINGKASAN A/B ==', flush=True)
for h in HASIL:
    print(f"  {h['varian']:5s} {h['model']:22s} {h.get('dtk', 0):6.1f} dtk "
          f"out={h.get('out_kar', 0):5d} kar editan={h.get('editan', '-')} "
          f"tidak_ada={h.get('tidak_ada', '-')} "
          f"galat={str(h.get('galat', '-'))[:70]}", flush=True)

Path('/app/data/_ab_hasil.json').write_text(
    json.dumps({'user_kar': len(user_asal), 'hasil': HASIL},
               indent=2, ensure_ascii=False))
print('detail → /app/data/_ab_hasil.json', flush=True)
