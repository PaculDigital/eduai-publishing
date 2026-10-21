"""UJI 2 — BANDING 3 CARA KIRIM BAGIAN KE AI (risiko: AI bingung/sempit konteks).

TUJUAN (kekhawatiran Bos 08 Okt, verbatim): "Saya belum tahu effeknya terhadap ai
yang akan mengerjakan revisi, jangan sampai buat blunder akhirnya jadi salah ai
dalam outputnya, gara-gara pengaruh jev yang jadi membingungkan ai atau jadi tidak
tahu konteks (tapi belum di uji)."

⇒ UJI: minta revisi BAGIAN YANG SAMA dengan 3 cara, bandingkan hasil AI.

CARA:
  A · BAB PENUH       — kirim seluruh BAB sebagai bahan (SEKARANG / jalur lama)
  B · POTONGAN SAJA   — kirim HANYA potongan sub-bab
  C · POTONGAN + PETA — potongan + peta naskah (daftar bab/sub-bab) + judul induk

KOMENTAR UJI (sama untuk ketiganya) — komentar pembimbing yang NYATA:
  "Bagian ini masih terlalu umum, tolong perdalam dengan contoh konkret dan
   tambahkan rujukan yang relevan."

BAHAN: Tesis 78 (fid=78) — sub-bab 2.1.5 Komitmen Perusahaan (baris 1828-1872).

UKUR (yang bisa dinilai apa adanya, tanpa selera):
  · apakah keluaran AI berada DALAM bagian yang diminta (tidak melebar)?
  · apakah AI menyentuh bagian LAIN (tanda bingung / kehilangan fokus)?
  · panjang keluaran · apakah menyebut istilah sub-bab · waktu · model asli
"""
import sys, json, time, re
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas

KOMENTAR = ("Bagian ini masih terlalu umum, tolong perdalam dengan contoh konkret "
            "dan tambahkan rujukan yang relevan.")
SUBBAB = (1828, 1872)      # 2.1.5 Komitmen Perusahaan (terukur: mulai-akhir)


def teks_naskah(db, fid):
    fb = db.get(FileBerkas, fid)
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    return (_teks_dari_berkas(p, fb.nama or '') or ''), (fb.nama or '')


def panggil_ai(perintah: str, bahan: str, judul: str = '') -> tuple[str, str, float]:
    """Panggil AI via 9router (SATU PINTU). Kembalikan (keluaran, model, dtk)."""
    import urllib.request
    import os
    import sys as _sys
    _sys.path.insert(0, '/app')
    from app.ai import _urai_jawaban                     # urai resmi app (streaming)

    base = os.environ.get('EDUAI_ROUTER_BASE') or 'http://9router:20128/v1'
    kunci = os.environ.get('EDUAI_ROUTER_KEY') or 'x'
    model = os.environ.get('EDUAI_AI_MODEL') or 'EduAi'

    kepala = (f'Kamu membantu mahasiswa memperbaiki naskah tesis. '
              f'{("Bagian yang direvisi: " + judul) if judul else ""}\n'
              f'PERMINTAAN PEMBIMBING: {perintah}\n'
              f'Tulis ULANG bagian yang diberikan sesuai permintaan. '
              f'Keluarkan HANYA teks hasil revisi, tanpa penjelasan tambahan.\n\n'
              f'--- BAHAN ---\n')
    pesan = kepala + bahan + '\n--- AKHIR BAHAN ---\n'

    body = json.dumps({
        'model': model, 'temperature': 0.3,
        #  🚨 SETELAN PRODUKSI (ACC Bos 29Sep26, app/ai.py:966):
        #  reasoning WAJIB mati — kalau nyala, jatah token habis untuk
        #  berpikir → content KOSONG (terukur 15Okt26).
        'enable_thinking': False,
        'messages': [{'role': 'user', 'content': pesan}],
    }).encode()
    req = urllib.request.Request(
        base.rstrip('/') + '/chat/completions', data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {kunci}'})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=240) as r:
        mentah = r.read().decode()
    dtk = time.time() - t0
    isi, info = _urai_jawaban(mentah, model)      # urai resmi app
    return isi, info.get('model') or model, dtk


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        teks, nama = teks_naskah(db, fid)
        baris = teks.split('\n')
        print('═' * 74)
        print(f'📄 fid={fid} {nama[:46]}')
        print(f'🧪 UJI: revisi sub-bab 2.1.5 Komitmen Perusahaan (baris {SUBBAB[0]}-{SUBBAB[1]})')
        print(f'📝 Komentar: {KOMENTAR}')

        potongan = '\n'.join(baris[SUBBAB[0]:SUBBAB[1]])
        # BAB II penuh (untuk cara A): cari batas BAB II - BAB III
        awal_bab = next(i for i in range(len(baris)) if re.match(r'^\s*BAB\s+II\b', baris[i], re.I) and i > 300)
        akhir_bab = next(i for i in range(awal_bab + 1, len(baris)) if re.match(r'^\s*BAB\s+III\b', baris[i], re.I))
        bab_penuh = '\n'.join(baris[awal_bab:akhir_bab])
        print(f'   BAB II = baris {awal_bab}-{akhir_bab} ({len(bab_penuh):,} kar)')
        print(f'   Potongan 2.1.5 = {len(potongan):,} kar')

        # peta naskah (ringkas) untuk cara C
        peta_txt = ('PETA NASKAH (posisi bagian yang direvisi):\n'
                    '  BAB II · TINJAUAN PUSTAKA\n'
                    '    2.1. Tinjauan Teori dan Konsep\n'
                    '      2.1.4. Kepercayaan\n'
                    '      2.1.5. Komitmen Perusahaan   ← BAGIAN YANG DIREVISI\n'
                    '      2.1.6. Komunikasi\n'
                    '    2.2. Penelitian Terdahulu\n')

        hasil = {}
        jenis = [
            ('A · BAB PENUH       ', bab_penuh, ''),
            ('B · POTONGAN SAJA   ', potongan, ''),
            ('C · POTONGAN + PETA ', potongan, ''),
        ]
        for label, bahan, extra in jenis:
            if label.startswith('C'):
                bahan = peta_txt + '\n--- BAGIAN YANG DIREVISI ---\n' + bahan
            print(f'\n{"─" * 70}\n▶ {label} · bahan {len(bahan):,} kar')
            try:
                kel, model, dtk = panggil_ai(KOMENTAR, bahan, 'Komitmen Perusahaan')
            except Exception as e:                              # noqa: BLE001
                print(f'   ❌ GAGAL: {type(e).__name__}: {e}')
                hasil[label] = None
                continue
            hasil[label] = (kel, model, dtk)
            print(f'   ⏱️  {dtk:.1f} dtk · model ASLI: {model} · keluaran {len(kel):,} kar')
            # ukur objektif
            sebut_sub = 'komitmen' in kel.lower()
            melebar = any(x in kel.lower() for x in ('kepercayaan', 'komunikasi',
                                                     'loyalitas', 'penelitian terdahulu'))
            print(f'   · menyebut "komitmen": {sebut_sub}')
            print(f'   · menyentuh bagian LAIN (melebar): {melebar}')
            print(f'   · potongan awal: {kel[:200].replace(chr(10), " ")}')

        print(f'\n{"═" * 74}\nRINGKASAN PERBANDINGAN')
        for label, v in hasil.items():
            if v is None:
                print(f'   {label} ❌ GAGAL'); continue
            kel, model, dtk = v
            print(f'   {label} {dtk:6.1f} dtk · keluar {len(kel):6,} kar · model {model[:28]}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
