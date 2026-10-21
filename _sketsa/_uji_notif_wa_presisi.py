"""UJI: apakah notif WA sekarang PRESISI? (bukan asal kirim)

Menguji fungsi SUNGGUHAN `_sebab_jalur1()` di app/ai.py + memotong potongan
logika keputusan WA, lalu MENJALANKANNYA (pola _periksa_pagar_c10.py).

Kasus uji diambil dari KEJADIAN NYATA 05Okt26.
"""
import sys

sys.path.insert(0, '/app')

# ── Ambil fungsi asli dari app/ai.py ─────────────────────────────────────
import re                                    # noqa: E402
import pathlib                               # noqa: E402

src = pathlib.Path('/app/app/ai.py').read_text()

# Fungsi _sebab_jalur1 ada DI DALAM _panggil_router → potong & jalankan.
m = re.search(r'\n    def _sebab_jalur1\(e: Exception\) -> str:.*?return \'sambungan\'.*?\n\n',
              src, re.S)
if not m:
    print('❌ TIDAK KETEMU _sebab_jalur1 → uji ini TIDAK BERGUNA')
    sys.exit(1)

ns: dict = {}
exec('class _T:\n' + ''.join('    ' + b + '\n' for b in
     m.group(0).strip().split('\n')) + '    pass\nt = _T()', ns)
sebab = ns['_T']._sebab_jalur1          # ambil dari KELAS (self belum ada)

print('═' * 92)
print('  UJI NOTIF WA PRESISI — fungsi asli _sebab_jalur1()')
print('═' * 92)

# (jenis galat NYATA, sebab yang HARUS keluar, boleh kirim WA?)
kasus = [
    # 🚫 BUKAN masalah jalur → JANGAN kirim WA (ini yang bikin alarm palsu)
    (RuntimeError("jawaban TERPOTONG (finish=length, reasoning=20, out=20/32000). "
                  "Naikkan EDUAI_AI_MAX_TOKENS"), 'jatah', False),
    (RuntimeError('konten kosong dari model'), 'kosong', False),
    (RuntimeError('respons kosong dari model (raw=\'\')'), 'kosong', False),
    # ✅ MASALAH NYATA → KIRIM WA
    (RuntimeError('9router HTTP 503: service unavailable'), 'sambungan', True),
    (RuntimeError("ConnectError: [Errno -2] Name or service not known"), 'sambungan', True),
    (RuntimeError('9router HTTP 404: model not found'), 'sambungan', True),
]

lulus = gagal = 0
for e, harus, boleh_wa in kasus:
    d = sebab(e)
    ok_sebab = (d == harus)
    ok_wa = ((d not in ('jatah', 'kosong')) == boleh_wa)
    ok = ok_sebab and ok_wa
    lulus += ok
    gagal += (not ok)
    tanda = '✅' if ok else '❌'
    print(f'  {tanda} {str(e)[:52]:<54} → {d:<10} WA={"KIRIM" if boleh_wa else "JANGAN"}')

print()
print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')

# ── PAGAR: pastikan kode LAMA (notif asal kirim) benar-benar SUDAH HILANG ──
print()
print('── PAGAR: kode lama "jalur 1 AI sedang bermasalah" harus SUDAH TIDAK ADA ──')
n_lama = src.count('jalur 1 AI sedang bermasalah')
print(f'  frasa lama ditemukan: {n_lama}×  →', '✅ bersih' if n_lama == 0
      else '❌ MASIH ADA (notif masih asal kirim)')
if n_lama:
    gagal += 1

n_gerbang = src.count("if sebab1 in ('jatah', 'kosong')")
print(f'  penjaga WA (sebab1 jatah/kosong) : {n_gerbang}×  →',
      '✅ ada' if n_gerbang == 1 else '❌ hilang')
if n_gerbang != 1:
    gagal += 1

print()
print('HASIL AKHIR:', 'LULUS ✅' if gagal == 0 else f'GAGAL ❌ ({gagal})')
sys.exit(0 if gagal == 0 else 1)
