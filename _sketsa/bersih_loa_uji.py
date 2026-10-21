"""BERSIHKAN data uji LoA di produksi — HANYA nomor 1.001 (data uji Wulan).

AMAN:
  · simpan cadangan dulu ke _arsip/pre-bersih-loa-<tgl>/
  · nomor_artikel dikembalikan ke 0 supaya LoA asli mulai dari 1.001
  · setelan (volume/editor/kontak) TIDAK diubah
  · tidak menyentuh DB user, tidak menyentuh berkas artikel
"""
import subprocess, json, pathlib, datetime

STAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
ARSIP = pathlib.Path(f'/opt/data/services/eduai-publishing/_arsip/pre-bersih-loa-{STAMP}')
ARSIP.mkdir(parents=True, exist_ok=True)
print('arsip:', ARSIP)

def baca(nama):
    r = subprocess.run(['docker', 'exec', 'eduai-app', 'cat', f'/app/data/{nama}'],
                       capture_output=True, text=True)
    return r.stdout

def tulis(nama, isi):
    r = subprocess.run(['docker', 'exec', '-i', 'eduai-app', 'sh', '-c',
                        f'cat > /app/data/{nama}'], input=isi, capture_output=True, text=True)
    return r.returncode

# ══ 1. CADANGKAN ══
for n in ['loa-terbit.json', 'setelan-loa.json']:
    isi = baca(n)
    (ARSIP / n).write_text(isi, encoding='utf-8')
    print(f'  cadangan {n}: {len(isi)} byte')

# ══ 2. lihat isi ══
terbit = json.loads(baca('loa-terbit.json') or '{}')
setelan = json.loads(baca('setelan-loa.json') or '{}')
print('\nsebelum:')
print('  LoA terbit :', list(terbit.keys()))
print('  nomor_art  :', setelan.get('nomor_artikel'))

# ══ 3. hapus HANYA data uji ══
UJI = ['1.001']
dihapus = []
for k in UJI:
    if k in terbit:
        # pastikan benar-benar data uji, bukan artikel nyata
        if 'UJI' in (terbit[k].get('judul', '') + terbit[k].get('penulis', '')).upper():
            terbit.pop(k)
            dihapus.append(k)
        else:
            print(f'  ⚠️ {k} BUKAN data uji — DILEWATI')

# nomor urut dikembalikan ke 0 -> LoA asli berikutnya = 1.001
setelan['nomor_artikel'] = 0

print('\nsesudah:')
print('  LoA terbit :', list(terbit.keys()) or '(kosong)')
print('  nomor_art  :', setelan['nomor_artikel'])

# ══ 4. tulis balik ══
tulis('loa-terbit.json', json.dumps(terbit, indent=1, ensure_ascii=False))
tulis('setelan-loa.json', json.dumps(setelan, indent=1, ensure_ascii=False))
print('\n✓ dihapus:', dihapus)
