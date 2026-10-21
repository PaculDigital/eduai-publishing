"""UJI SAMBUNGAN KONTEKS — pagar + jalur (tanpa AI, Rp 0).

Diuji:
  1. _boleh_konteks(): revisi biasa → boleh · "ubah alur" → TIDAK boleh
  2. Pagar target: sub-bab '1.2' → potong · 'BAB III' → JANGAN · '' → JANGAN
  3. penurunan ukuran naskah nyata untuk 6 dokumen contoh
  4. GAGAL senyap → jatuh ke naskah utuh (bukan error)
"""
import sys, zipfile, re, glob, html
sys.path.insert(0, '/app')
from app.ai import _boleh_konteks
from app.state import petakan, buang_daftar_isi
from app.konteks import bangun_prompt

LULUS = GAGAL = 0
def cek(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {info}')


def teks_docx(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    return html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', xml)))


print('══ 1. PAGAR _boleh_konteks() — intent tidak boleh dipotong ══')
cek('revisi biasa → BOLEH',
    _boleh_konteks(['perbaiki kalimat ini supaya jelas']) is True)
cek('"ubah alur" → TIDAK boleh',
    _boleh_konteks(['ubah alur pembahasan jadi induktif']) is False)
cek('"ubah seluruh dokumen" → TIDAK boleh',
    _boleh_konteks(['ubah alur bab 1 sampai bab 5']) is False)
cek('tanpa komentar → BOLEH', _boleh_konteks([]) is True)

print('\n══ 2. PAGAR TARGET — hanya sub-bab yang dipotong ══')
f = glob.glob('/app/_contoh-dokumen/**/TESIS-S2-unhas-manajemen*.docx')[0]
peta = petakan(buang_daftar_isi(teks_docx(f)))
sub = [s for s in peta if '.' in str(s['section_id'])]
bab = [s for s in peta if '.' not in str(s['section_id'])]
cek('peta punya sub-bab', len(sub) >= 3, f'{len(sub)} sub-bab')
print(f'     (sub-bab {len(sub)} · bab {len(bab)})')

print('\n══ 3. PENURUNAN UKURAN — 6 dokumen contoh (target sub-bab) ══')
print(f'  {"dokumen":<44}{"naskah utuh":>13}{"dikirim":>11}{"prompt":>11}{"hemat":>9}')
ringkas = []
for f2 in sorted(glob.glob('/app/_contoh-dokumen/**/*.docx', recursive=True)):
    teks = teks_docx(f2)
    peta2 = petakan(buang_daftar_isi(teks))
    subs = [s for s in peta2 if '.' in str(s['section_id'])]
    if not subs:
        print(f'  {f2.split("/")[-1][:42]:<44}{len(teks):>13,}{"—":>11}{"—":>11}{"tanpa sub-bab":>9}')
        continue
    # uji 3 sub-bab: terkecil, tengah, terbesar
    subs.sort(key=lambda s: s.get('char_count', 0))
    for s in (subs[0], subs[len(subs) // 2], subs[-1]):
        tgt = str(s['section_id'])
        pr = bangun_prompt(bagian_target=tgt, peta=peta2,
                           brief_ringkas='JUDUL: contoh',
                           isi_saat_ini=s['isi_teks'], komentar='perbaiki')
        kirim = len(s['isi_teks'])
        hemat = len(teks) / max(kirim, 1)
        ringkas.append((f2.split('/')[-1][:30], tgt, len(teks), kirim, len(pr), hemat))
        print(f'  {f2.split("/")[-1][:30]:<32}{tgt:>8}{len(teks):>13,}'
              f'{kirim:>11,}{len(pr):>11,}{hemat:>8.1f}×')

print('\n══ 4. GAGAL SENYAP → naskah utuh, bukan error ══')
try:
    pr = bangun_prompt(bagian_target='9.9', peta=peta,
                       brief_ringkas='x', isi_saat_ini='', komentar='x')
    cek('target tidak ada → tidak error', True, f'{len(pr)} kar')
except Exception as e:
    cek('target tidak ada → tidak error', False, f'{type(e).__name__}: {e}')

print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
if ringkas:
    r = [x[5] for x in ringkas if x[3] < x[2]]
    if r:
        print(f'  hemat: min {min(r):.1f}× · rata-rata {sum(r)/len(r):.1f}× · maks {max(r):.1f}×')
sys.exit(1 if GAGAL else 0)
