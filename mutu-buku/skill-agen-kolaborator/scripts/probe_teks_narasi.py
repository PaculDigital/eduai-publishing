#!/usr/bin/env python3
"""PROBE TEKS PROSA — untuk modul yang menghasilkan narasi/laporan.

Kelas bug yang TIDAK bisa ditangkap uji status HTTP: respons 200, teksnya cacat.
Terukur 21 Okt 2026 (Fase 3 BAB IV, `bab4_narasi.susun_draf`) — uji bawaan
memeriksa `200` + `'signifikan' in teks` → LULUS, padahal teks yang keluar:

    - H3: pengaruh Harga terhadap Keputusan sebesar 0.0065 dengan nilai
      signifikansi — — hipotesis ditolak.
    - H3: H3: b=0.006458, p=None → tidak signifikan

CARA PAKAI
    Salin ke root repo salinan, sesuaikan KONFIG + siapkan_kasus(), lalu:
        .venv/bin/python probe_teks_narasi.py
    atau (di container uji):
        docker exec -w /app -e <SVC>_URL=... <c> python3 probe_teks_narasi.py

    Keluar EXIT 1 kalau ada temuan, supaya bisa dipasang di gerbang.

BENTUK KASUS yang WAJIB disiapkan siapkan_kasus():
    {
      'teks':  '<prosa yang dihasilkan modul>',
      'hasil': {...},            # dict hasil mesin yang jadi BAHAN prosa
      'harapan': [               # daftar klaim yang harus muncul di teks
          {'label': 'H1', 'nilai': ('b', 'p'), 'punya_p': True},
          {'label': 'H3', 'nilai': ('b',),     'punya_p': False},   # bootstrap
      ],
    }
"""
import json
import re
import sys

KONFIG = {
    # kata yang menandakan vonis — sesuaikan dengan bahasa modul
    'kata_vonis': ['ditolak', 'diterima', 'tidak signifikan', 'signifikan'],
    # pemisah tanda pisah yang dipakai modul
    'pemisah': '—',
    # angka yang boleh muncul walau bukan dari 'hasil' (mis. jumlah responden)
    'angka_boleh': set(),
    # ambang: token None/nan yang tidak boleh muncul di prosa
    'terlarang_literal': ['None', 'null', 'NaN', 'nan', 'undefined'],
    # pasangan (benar, salah) untuk kalimat bersyarat — uji DUA keadaan.
    # Contoh: (''] melewati nol'', '']  melewati'')  ← satu spasi vs dua
    'penanda_dua_keadaan': [],
}

TEMUAN = []


def cek(nama, kondisi, info=''):
    print(('  OK  ' if kondisi else '  BUG ') + nama +
          ('' if kondisi else f'  -> {info}'))
    if not kondisi:
        TEMUAN.append((nama, str(info)[:200]))


# ── pengumpul angka dari hasil mesin (rekursif, SEMUA kunci) ──────────────
def semua_float(obj, keluar=None):
    """Kumpulkan SEMUA angka dari hasil mesin — jangan cuma kunci yang dipakai.

    Terukur: Wulan sempat menuduh `0.0119` 'bukan dari mesin' — ternyata itu
    **R²**. Sebelum menuduh angka karangan, sisir seluruh dict.
    """
    if keluar is None:
        keluar = set()
    if isinstance(obj, dict):
        for v in obj.values():
            semua_float(v, keluar)
    elif isinstance(obj, list):
        for v in obj:
            semua_float(v, keluar)
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        keluar.add(round(float(obj), 4))
        keluar.add(round(float(obj), 3))
    return keluar


def kalimat_untuk(teks, label):
    """Ambil baris/kalimat yang memuat label hipotesis."""
    for baris in re.split(r'(?<=[.;])\s+|\n', teks):
        if re.search(rf'\b{re.escape(label)}\b', baris):
            return baris
    return ''


def periksa(kasus):
    teks = kasus['teks']
    hasil = kasus.get('hasil') or {}
    harapan = kasus.get('harapan') or []

    # 1. label dobel  "H1: H1:"
    dobel = re.findall(r'\b(\w+):\s*\1:', teks)
    cek('tidak ada label dobel ("H1: H1:")', not dobel, dobel[:4])

    # 2. separator dobel  "— —"
    sep = re.escape(KONFIG['pemisah'])
    sep_dobel = re.findall(rf'{sep}\s*{sep}', teks)
    cek('tidak ada separator dobel', not sep_dobel, sep_dobel[:4])

    # 3. literal terlarang tercetak
    for lit in KONFIG['terlarang_literal']:
        cek(f'tidak ada "{lit}" tercetak di prosa', lit not in teks,
            [s for s in teks.split('\n') if lit in s][:2])

    # 3b. SPASI DOBEL — cacat halus sesudah perbaikan f-string bersyarat.
    #     Terukur 21 Okt 2026: f"{'tidak' if sig else ''} melewati nol"
    #     -> saat sig=True keluar "  melewati" (dua spasi). Obat: spasi MASUK
    #     ke dalam potongan -> f"{'tidak ' if sig else ''}melewati nol".
    #     ⚠️ Bandingkan di dalam BARIS, jangan di teks utuh: indentasi/baris baru
    #     menghasilkan spasi beruntun yang SAH.
    dobel_spasi = [b for b in teks.splitlines()
                   if '  ' in b.strip() and not b.strip().startswith(('-', '*', '>'))]
    cek('tidak ada spasi dobel di dalam baris', not dobel_spasi,
        [b.strip()[:90] for b in dobel_spasi[:3]])
    #     Dan bandingkan dua KUTIPAN penanda, bukan satu: keadaan terbalik juga wajib rapi.
    for penanda in KONFIG.get('penanda_dua_keadaan', ()):
        # penanda: (potongan_benar, potongan_salah) mis. ('] melewati nol', ']  melewati')
        benar, salah = penanda
        if benar in teks:
            cek(f'penanda "{benar}" tidak berupa spasi dobel', salah not in teks,
                f'"{salah}" ikut muncul')

    # 4. angka desimal di prosa HARUS berasal dari hasil mesin
    angka_teks = {round(float(x), 4)
                  for x in re.findall(r'-?\d+\.\d{3,4}', teks)}
    angka_mesin = semua_float(hasil) | KONFIG['angka_boleh']
    asing = {a for a in angka_teks
             if round(a, 4) not in angka_mesin and round(a, 3) not in angka_mesin}
    cek('semua angka desimal prosa berasal dari mesin', not asing, sorted(asing)[:8])

    # 5. 🚨 nilai yang TIDAK ADA tidak boleh divonis
    for h in harapan:
        kal = kalimat_untuk(teks, h['label'])
        if not kal:
            cek(f"{h['label']} muncul di prosa", False, 'kalimat tidak ditemukan')
            continue
        if h.get('punya_p') is False:
            vonis = [k for k in KONFIG['kata_vonis'] if k in kal.lower()]
            cek(f"{h['label']} tanpa p → TIDAK divonis", not vonis,
                f'kalimat={kal.strip()[:110]!r} vonis={vonis}')
            # wajib menjelaskan alasannya
            jujur = any(k in kal.lower() for k in
                        ('bootstrap', 'tidak tersedia', 'tidak diukur',
                         'tidak dapat', '—'))
            cek(f"{h['label']} tanpa p → disebut alasannya", jujur, kal.strip()[:110])

    # 6. label yang diminta benar-benar ada
    for h in harapan:
        cek(f"{h['label']} ada di prosa",
            re.search(rf'\b{re.escape(h["label"])}\b', teks) is not None)


def siapkan_kasus():
    """SESUAIKAN: bangun satu kasus nyata dari modul yang direview."""
    raise SystemExit(
        'Sesuaikan siapkan_kasus() dulu — kembalikan '
        "{'teks':..., 'hasil':..., 'harapan':[...]}")


def main():
    kasus = siapkan_kasus()
    print('== PROBE TEKS PROSA ==')
    print(f'   panjang teks: {len(kasus["teks"])} kar')
    periksa(kasus)
    print()
    if TEMUAN:
        print(f'RINGKAS: {len(TEMUAN)} BUG')
        for n, i in TEMUAN:
            print('   -', n, '|', i)
        sys.exit(1)
    print('BERSIH — tidak ada cacat prosa terdeteksi')


if __name__ == '__main__':
    main()
