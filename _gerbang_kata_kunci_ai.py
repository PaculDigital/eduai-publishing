#!/usr/bin/env python3
"""GERBANG KATA KUNCI AI — 13 Okt 2026 (putusan Bos 1A + 2A).

Menjaga 5 janji:
  ① Kamus DULU (Rp 0); AI hanya dipakai kalau kamus tidak mengenali.
  ② Jalur "kata mentah" yang bikin NGAWUR sudah DICABUT dari cari_semua().
  ③ AI gagal ⇒ hasil KOSONG + jujur (`belum_dipetakan`), bukan dikarang.
  ④ Urai balasan AI tahan banting (JSON kotor tetap terbaca / ditolak aman).
  ⑤ Pesan 0-hasil MEMBEDAKAN "tidak dipetakan" vs "tidak ada artikel",
     dan TIDAK ADA kalimat "TANPA TOKEN" di bagian ① (putusan Bos 1b).

⚠️ DIUJI 2 ARAH: setelah sehat, gerbang DISUNTIK RUSAK ⇒ WAJIB EXIT 1.
   Gerbang yang tak bisa gagal = tidak menjaga apa pun.

JALAN DI DALAM CONTAINER:
  docker cp _gerbang_kata_kunci_ai.py eduai-app:/app/_gerbang_kk.py
  docker exec eduai-app python3 /app/_gerbang_kk.py
"""
import re
import sys

LULUS = GAGAL = 0
PESAN: list[str] = []


def cek(nama: str, syarat: bool, ket: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
    else:
        GAGAL += 1
        PESAN.append(f'  ✗ {nama}' + (f' — {ket}' if ket else ''))


# ══════════════════════════════════════════════════════════════════════
def utama() -> int:
    import os
    os.chdir('/app')
    sys.path.insert(0, '/app')

    import app.pustaka as P                                        # noqa: N813
    import app.jurnal as J                                         # noqa: N813

    src_pus = open('app/pustaka.py', encoding='utf-8').read()
    src_jur = open('app/rute_jurnal.py', encoding='utf-8').read()
    src_ref = open('app/templates/referensi.html', encoding='utf-8').read()

    print('═══ GERBANG KATA KUNCI AI ═══')

    # ── ① KAMUS DULU, AI PENGGANTI ────────────────────────────────
    print('\n① Kamus dulu (Rp 0), AI hanya kalau kamus gagal')
    cek('fungsi kata_kunci_ai ada', hasattr(P, 'kata_kunci_ai'))
    cek('fungsi konsep_terbaik ada', hasattr(P, 'konsep_terbaik'))
    cek('cari_semua punya param pakai_ai',
        'pakai_ai' in P.cari_semua.__code__.co_varnames)
    cek('cari_untuk_bab punya param pakai_ai',
        'pakai_ai' in J.cari_untuk_bab.__code__.co_varnames)

    # judul yang DIKENAL kamus → sumber harus 'kamus', tanpa panggil AI
    k_kamus = P.kata_kunci('pengaruh kualitas produk terhadap keputusan pembelian')
    cek('judul dikenal kamus → konsep terisi', len(k_kamus.get('konsep') or []) > 0,
        f"konsep={len(k_kamus.get('konsep') or [])}")
    kk2, src2 = P.konsep_terbaik('pengaruh kualitas produk terhadap keputusan pembelian')
    cek('konsep_terbaik: kamus menang (tanpa AI)', src2 == 'kamus', f'sumber={src2}')

    # ── ② JALUR "KATA MENTAH" DICABUT ─────────────────────────────
    print('\n② Jalur kata mentah (akar NGAWUR) sudah dicabut')
    cek('cari_semua menandai belum_dipetakan',
        'belum_dipetakan' in src_pus)
    cek('ada early-return saat konsep kosong',
        re.search(r'if not kw\.get\(.konsep.\):\s*\n\s*log\.info\(.\[pustaka\] tema',
                  src_pus) is not None)

    # jalur NYATA tanpa jaringan: konsep kosong + pakai_ai=False → 0 artikel
    h = P.cari_semua('xyzqwerty tidak ada di kamus', pakai_ai=False)
    cek('konsep kosong & tanpa AI → artikel=0', len(h.get('artikel') or []) == 0,
        f"artikel={len(h.get('artikel') or [])}")
    cek('konsep kosong & tanpa AI → jujur (belum_dipetakan)',
        bool(h.get('belum_dipetakan')))
    cek('konsep kosong → sumber_kata_kunci kosong',
        h.get('sumber_kata_kunci') == '',
        f"sumber={h.get('sumber_kata_kunci')!r}")

    # ── ③ URAI BALASAN AI (tanpa jaringan) ────────────────────────
    print('\n③ Urai balasan AI tahan banting')
    baik = '{"konsep":[{"nama":"kualitas layanan","en":["service quality"],' \
           '"id":["kualitas layanan"]}]}'
    k = P._urai_konsep_ai(baik)
    cek('JSON bersih terbaca', len(k) == 1 and k[0]['konsep'] == 'kualitas layanan')
    cek('en/id terisi', k and k[0]['en'] == ['service quality'])

    kotor = 'Baik, ini hasilnya:\n```json\n' + baik + '\n```\nSemoga membantu!'
    cek('JSON di dalam cerita tetap diambil',
        len(P._urai_konsep_ai(kotor)) == 1)
    cek('teks kosong → []', P._urai_konsep_ai('') == [])
    cek('bukan JSON → [] (tidak melempar)', P._urai_konsep_ai('maaf saya tidak tahu') == [])
    cek('JSON rusak → [] (tidak melempar)', P._urai_konsep_ai('{"konsep": [rusak') == [])
    cek('konsep tanpa en → dibuang', P._urai_konsep_ai(
        '{"konsep":[{"nama":"x","en":[],"id":["x"]}]}') == [])
    cek('maksimal 4 konsep', len(P._urai_konsep_ai(
        '{"konsep":[' + ','.join(
            '{"nama":"k%d","en":["e%d"]}' % (i, i) for i in range(9)) + ']}')) == 4)

    # ── ④ PESAN JUJUR (dua kasus DIBEDAKAN) ───────────────────────
    print('\n④ Pesan 0-hasil dibedakan + "TANPA TOKEN" dibuang')
    cek('kode tidak_dipetakan ADA', 'tidak_dipetakan' in src_jur)
    cek('kode tidak_ada_hasil ADA', 'tidak_ada_hasil' in src_jur)
    cek('pesan tidak_dipetakan menyebut "memetakan"',
        'memetakan' in src_jur)
    cek('pesan tidak_ada_hasil menyebut Garuda',
        'Garuda' in src_jur)
    cek('lencana "TANPA TOKEN" SUDAH DIBUANG dari bagian ①',
        'TANPA TOKEN' not in src_ref)
    cek('rute /kata-kunci-ai ada', '/kata-kunci-ai' in src_jur)
    cek('tombol bantu isi ada di template', 'btn-bantu' in src_ref)
    cek('fungsi bantuIsi ada', 'function bantuIsi' in src_ref)
    cek('chip bisa dibuang user (buangKonsep)',
        'function buangKonsep' in src_ref)

    # ── ⑤ SARING: konfirmasi pagar lama tidak rusak ───────────────
    print('\n⑤ Pagar lama tetap utuh')
    cek('audit_doi tetap ADA', hasattr(P, 'audit_doi'))
    cek('daftar_pustaka_apa7 tetap ADA', hasattr(P, 'daftar_pustaka_apa7'))
    cek('cari_semua tetap pakai _nyambung (saring tema)',
        '_nyambung(r, kw)' in src_pus)
    cek('KAMUS_KONSEP tetap ADA', bool(getattr(P, 'KAMUS_KONSEP', None)))

    print()
    for p in PESAN:
        print(p)
    print(f'═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(utama())
