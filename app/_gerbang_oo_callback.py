"""GERBANG CALLBACK ONLYOFFICE — /oo/simpan wajib balas {"error": 0}.

11-12Okt26. AKAR YANG DIJAGA (terukur + dokumen resmi OO):
  Dokumen ONLYOFFICE (api.onlyoffice.com/docs/docs-api/usage-api/callback-handler):
    "The document storage service MUST return {"error": 0}, otherwise the
     document editor WILL DISPLAY AN ERROR MESSAGE."
  ⇒ Balasan SELAIN {"error":0} membuat editor menampilkan modal
    "Unduhan gagal" (errorCode -4) — pesan yang MENYESATKAN, padahal
    unduhan SEHAT (terbukti 200 OK di 11Okt26).

DUA BUG NYATA yang dijaga gerbang ini (dulu ada, sudah diperbaiki):
  1. `if not aksi['harus_simpan']: return {'error': 0}`  ← ini SUDAH benar.
  2. Lapis-2 penguncian: `return JSONResponse({'error': -4})` ← SALAH. Balasan
     -4 ⇒ OO tampilkan "Unduhan gagal". Sekarang: berkas TIDAK disentuh,
     tetap balas {"error": 0}.
  3. `if not url: return {'error': 1}` ← SALAH. status 2/6 tanpa url = tidak
     ada isi untuk disimpan (OO memang mengirim status:1 dulu untuk koneksi)
     ⇒ sekarang balas {"error": 0} + catat.

JALANKAN DI DALAM CONTAINER:
    docker exec eduai-app python3 /app/app/_gerbang_oo_callback.py
"""
import re
import sys
from pathlib import Path

LULUS = 0
GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {bukti}' if bukti else ''))


def main():
    D = Path(__file__).resolve().parent
    sumber = (D / 'main.py').read_text(encoding='utf-8')

    # ── ambil HANYA blok rute /oo/simpan (jangan nilai berkas lain) ──────
    m = re.search(r"@app\.post\('/oo/simpan/\{token\}'\)(.*?)(?=\n@app\.|\Z)",
                  sumber, re.S)
    if not m:
        print('❌ GAGAL: rute /oo/simpan tidak ditemukan')
        return 1
    blok = m.group(1)
    # ⚠️ buang KOMENTAR dulu — kalimat penjelasan memuat kata "'error': -4"
    #    sehingga uji bisa salah baca (gerbang harus menilai KODE, bukan prosa).
    kode = '\n'.join(re.sub(r'#.*$', '', ln) for ln in blok.splitlines())

    print('── UJI 1: BALASAN WAJIB {"error": 0} ──')
    # tidak boleh ada balasan error selain 0 di jalur SUKSES/dilewati
    cek('balasan {"error": -4} SUDAH TIDAK ADA (jebakan lama)',
        "'error': -4" not in kode and '"error": -4' not in kode,
        "masih ada -4 ⇒ OO akan tampilkan 'Unduhan gagal'")
    # error 1 hanya boleh untuk kegagalan NYATA (unduh gagal / kuota kurang)
    n_err1 = len(re.findall(r"JSONResponse\(\{'error': 1\}\)", kode))
    cek('{"error": 1} hanya untuk kegagalan NYATA (unduh/kuota), maks 3 titik',
        n_err1 <= 3, f'jumlah error:1 = {n_err1}')

    print()
    print('── UJI 2: JALUR "TIDAK PERLU SIMPAN" BALAS 0 ──')
    pola_simpan = (r"if not aksi\['harus_simpan'\]:\s*\n"
                   r"(?:.*\n)*?\s*return JSONResponse\(\{'error': 0\}\)")
    cek('`if not aksi[harus_simpan]` balas {"error": 0}',
        bool(re.search(pola_simpan, kode)))

    print()
    print('── UJI 3: LAPIS-2 (AI sedang jalan) TIDAK RUSAK & BALAS 0 ──')
    cek('Lapis-2 masih memeriksa proses AI (yang_sedang_jalan)',
        'yang_sedang_jalan' in kode)
    m2 = re.search(r"if _jalan:(.*?)(?=\n    url = |\Z)", kode, re.S)
    cek('blok `if _jalan` ADA', bool(m2))
    if m2:
        blok2 = m2.group(1)
        cek('`if _jalan` BALAS {"error": 0}',
            "JSONResponse({'error': 0})" in blok2)
        cek('`if _jalan` TIDAK menulis berkas (p.write_bytes TIDAK ada)',
            'write_bytes' not in blok2)

    print()
    print('── UJI 4: TANPA url ⇒ BALAS 0 (bukan 1) ──')
    m3 = re.search(r"if not url:(.*?)(?=\n    p = |\Z)", kode, re.S)
    cek('blok `if not url` ADA', bool(m3))
    if m3:
        blok3 = m3.group(1)
        cek('`if not url` BALAS {"error": 0}',
            "JSONResponse({'error': 0})" in blok3)
        cek('`if not url` TIDAK balas error 1 (jebakan lama)',
            "{'error': 1}" not in blok3)

    print()
    print('── UJI 5: JALUR SUKSES TETAP MENYIMPAN & BALAS 0 ──')
    cek('jalur sukses masih `p.write_bytes(isi)`', 'p.write_bytes(isi)' in kode)
    cek('jalur sukses balas {"error": 0}',
        kode.rstrip().endswith("JSONResponse({'error': 0})"))
    cek('kuota tetap dijaga (selisih > sisa ⇒ tolak)',
        'selisih > sisa' in kode)

    print()
    print('── UJI 6: SEMUA KEMBALIAN PASTI JSONResponse (tidak ada return None) ──')
    # hitung `return` di blok yang bukan JSONResponse / bukan di dalam if kecil
    kembali = re.findall(r"^\s{4}return (\S.*)$", kode, re.M)
    bukan = [k for k in kembali if 'JSONResponse' not in k and 'HTTPException' not in k]
    cek('tidak ada `return` aneh di level rute',
        not bukan, ' | '.join(bukan[:3]))

    print()
    print(f'HASIL GERBANG OO CALLBACK: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
