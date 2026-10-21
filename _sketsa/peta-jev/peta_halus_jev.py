"""PETA HALUS — CARA RESMI TERBUKTI (sub-bab), 08 Okt 2026 · TERUKUR 4/4.

Skrip RESMI peta halus. Tujuan: tunjuk BAGIAN TERTENTU DI DALAM BAB
(sub-bab), supaya AI revisi potongan itu saja — BUKAN satu bab penuh.

⛔ YANG DIBUANG (6 versi GAGAL karena ini): kode MENDUGA bentuk naskah
   (pola nomor, baris kosong, panjang baris, gabung paragraf). Bentuk naskah
   BEDA-beda: baris kosong di satu naskah = pemisah paragraf, di naskah lain
   = pemisah TIAP baris. Kode TIDAK BISA tahu. (dilarang Bos: "mesin dilarang
   menebak bentuk naskah")

✅ CARA BENAR (v10, TERBUKTI 4/4 di BAB I Tesis 78):
   1. KODE beri ID tiap baris — TANPA menebak bentuk
   2. KODE buang FAKTA yang PASTI bukan judul (daftar isi, penanda, caption,
      angka murni) — ini pembuangan FAKTA, bukan tebakan bentuk
   3. KODE kirim JENDELA 3 BARIS BER-ID per kandidat → JEV menilai
        L000618| melalui Relationship Marketing?
      > L000620| 1.3. Tujuan Penelitian        ← ditanya
        L000622| 1. Untuk menguji dan menganalisis Pengaruh D
   4. KODE rakit peta: p >= 0,80 = judul → mulai/akhir dari POSISI BARIS

⚠️ ATURAN KERAS (dari 10 versi ukur):
   · JANGAN kirim FAKTA HITUNGAN (panjang isi) — bisa salah saat sub-bab
     berdempetan ("1.3. Tujuan" langsung diikuti "1. Untuk menguji…" ⇒ isi 0).
     Kalau harus pakai angka, pakai ambang lebih rendah & tandai ragu.
   · JANGAN pakai kalimat BERLARANGAN ("bukan paragraf, bukan kalimat") →
     menurunkan jawaban (0,844 → 0,32).
   · BACA `p` LANGSUNG (p>=0,80 = judul). JANGAN pakai |2p-1| — itu menyesatkan.

JALAN: python3 peta_halus_jev.py <fid> [fid2 …]  (jalankan di container eduai-app)
"""
from __future__ import annotations

import json
import re
import sys
import time
from typing import Any

# ── AMBANG (putusan §4.0.2): p >= 0,80 → yakin; di bawah → boleh_dikunci=False
AMBANG = 0.80
MAKS_KAR_JUDUL = 70          # judul wajar ≤ 70 kar (FAKTA panjang, bukan tebakan)
GELOMBANG = 8                # 8 kandidat per panggilan Jev (fan-out resmi)

# ── PEMBUANGAN FAKTA: yang PASTI bukan judul ────────────────────────────
_PEMBUANG = re.compile(
    r'^\s*(?:'
    r'\[\[.*?\]\]'                                   # penanda internal
    r'|Sumber\s*:'                                   # caption tabel
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d'
    r'|Keterangan\s*:'
    r')\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')       # titik-pengarah daftar isi


def pasti_bukan_judul(s: str) -> bool:
    """HANYA fakta yang pasti bukan judul. TIDAK menebak bentuk."""
    if not s.strip():
        return True
    if _PEMBUANG.match(s) or _TITIK_ISI.search(s):
        return True
    if re.match(r'^Tabel\s+\d|^Gambar\s+\d', s, re.I):
        return True
    if re.fullmatch(r'[\d\.,%\s\-–—]+', s):           # angka / nomor halaman
        return True
    if re.fullmatch(r'[nN]\s*=\s*[\d\.,\s≈]+', s):    # rumus
        return True
    return False


def kandidat(teks: str, mulai: int = 0, selesai: int | None = None) -> list[tuple[int, str]]:
    """Baris pendek ber-ID dalam rentang [mulai, selesai). TANPA menebak bentuk."""
    baris = teks.split('\n')
    akhir = len(baris) if selesai is None else selesai
    out = []
    for i in range(max(0, mulai), min(akhir, len(baris))):
        s = ' '.join(baris[i].split())
        if pasti_bukan_judul(s) or len(s) > MAKS_KAR_JUDUL:
            continue
        out.append((i, s))
    return out


def _jendela(baris: list[str], i: int) -> dict[str, str]:
    """JENDELA 3 baris ber-ID: atas · tengah · bawah."""
    def _b(j: int) -> str:
        if j < 0:
            return '(awal naskah)'
        if j >= len(baris):
            return '(akhir naskah)'
        return f'L{j:06d}| ' + ' '.join(baris[j].split())[:90]
    return {'baris_atas': _b(i - 1), 'tengah': _b(i), 'baris_bawah': _b(i + 1)}


def petakan(teks: str, *, mulai: int = 0, selesai: int | None = None,
            boleh_panggil_jev: bool = True) -> dict[str, Any]:
    """Petakan sub-bab: KODE saring → JEV menilai jendela → KODE rakit.

    Return: {'bagian': [{'mulai','akhir','judul','p','boleh_dikunci','asal'}],
             'jumlah': N, 'dtk': …, 'jev': True/False}
    """
    try:
        from app import satpam                              # noqa: PLC0415
    except ImportError:                                     # dijalankan sbg skrip
        import satpam                                       # type: ignore # noqa: PLC0415

    baris = teks.split('\n')
    kand = kandidat(teks, mulai, selesai)
    t0 = time.time()

    nilai: dict[int, float | None] = {}
    jev_hidup = False
    if boleh_panggil_jev:
        for gel in range(0, len(kand), GELOMBANG):
            pakai = kand[gel:gel + GELOMBANG]
            paket, tanya = {}, {}
            for n, (i, s) in enumerate(pakai):
                nm = f'c{n}'
                paket[nm] = _jendela(baris, i)
                tanya[nm] = {'type': 'noul', 'instructions': (
                    f'Baris `{nm}.tengah` diapit dua baris lain. '
                    f'Apakah baris tengah ini awal sub-bab?')}
            try:
                jw = satpam.tanya_bebas_mutu(
                    json.dumps(paket, ensure_ascii=False)[:60000], tanya) or {}
                jev_hidup = True
            except Exception:                               # noqa: BLE001
                jw = {}
            for n, (i, _s) in enumerate(pakai):
                b = jw.get(f'c{n}') or {}
                p = b.get('noul')
                nilai[i] = None if p is None else float(p)

    # ── RAKIT: ambil yang lolos ambang, hitung mulai/akhir dari POSISI BARIS
    lolos = [i for i, _s in kand if (nilai.get(i) or 0) >= AMBANG]
    bagian: list[dict[str, Any]] = []
    for k, i in enumerate(lolos):
        nxt = lolos[k + 1] if k + 1 < len(lolos) else len(baris)
        p = nilai.get(i)
        bagian.append({
            'mulai': i,
            'akhir': nxt,
            'judul': ' '.join(baris[i].split())[:120],
            'p': None if p is None else round(p, 3),
            'boleh_dikunci': bool(p is not None and p >= AMBANG),
            'asal': 'jev' if jev_hidup else 'tebakan',
        })
    return {'bagian': bagian, 'jumlah': len(bagian),
            'dtk': round(time.time() - t0, 1), 'jev': jev_hidup,
            'kandidat': len(kand)}


def main() -> None:
    sys.path.insert(0, '/app')
    from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR   # noqa: PLC0415
    from app.models import FileBerkas                                  # noqa: PLC0415

    fid_list = [int(a) for a in sys.argv[1:]] or [78]
    db = SessionLocal()
    try:
        for fid in fid_list:
            fb = db.get(FileBerkas, fid)
            if fb is None:
                print(f'fid={fid} TIDAK ADA'); continue
            p_berkas = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
            teks = _teks_dari_berkas(p_berkas, fb.nama or '') or ''
            print('═' * 74)
            print(f'📄 fid={fid} {(fb.nama or "")[:50]}')
            hasil = petakan(teks)
            print(f'   kandidat={hasil["kandidat"]} · bagian={hasil["jumlah"]}'
                  f' · {hasil["dtk"]} dtk · jev={hasil["jev"]}')
            for b in hasil['bagian']:
                print(f'   ✅ baris {b["mulai"]:6d}–{b["akhir"]:6d} p={b["p"]}'
                      f' | {b["judul"][:50]}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
