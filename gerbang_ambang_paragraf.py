"""GERBANG AMBANG PARAGRAF — buktikan bug "satu baris 8.251 karakter" TERTUTUP.

Sehat lulus, DIBUAT SAKIT harus gagal (bergigi).
"""
import re
import sys

sys.path.insert(0, '/app')
import buku_umum_pipeline as P            # noqa: E402

lulus, gagal = 0, []


def cek(nama, syarat, pesan=''):
    global lulus
    if syarat:
        lulus += 1
        print(f"  LULUS {nama}")
    else:
        gagal.append(nama)
        print(f"  GAGAL {nama} {pesan}")


print('=== 1. AMBANG DARI SETELAN TONE (bukan angka mati) ===')
#  Nilai HARUS dibaca dari `tone_menulis` — jangan ditulis tangan di gerbang
#  (kalau tone berubah, gerbang ikut tahu). Yang dibutuhkan **batas BAWAH**
#  (angka PERTAMA): umum=60, anak=25, pendidikan=40.
import tone_menulis as _TM                # noqa: E402
for jenis in ('umum', 'anak', 'pendidikan'):
    kal = _TM.tone(jenis)['paragraf']
    harap = int(kal.split('kata')[0].split('-')[0].strip())
    a = P._ambang_paragraf_min(jenis)
    cek(f'ambang {jenis} = {a} (tone "{kal}" ⇒ bawah {harap})', a == harap,
        f'harap {harap}, dapat {a}')

#  Jenis TAK DIKENAL harus jatuh ke 40, bukan meledak.
cek('ambang jenis ngawur = 40', P._ambang_paragraf_min('ngawur') == 40)

print()
print('=== 2. PARAGRAF SESUAI TONE TIDAK DIGABUNG ===')
#  3 paragraf @30 kata (setelan buku anak: 25-40 kata) — HARUS tetap 3.
satu = ' '.join(['kata'] * 30)
masuk = f'{satu}\n\n{satu}\n\n{satu}'
keluar = P.merge_short_paragraphs(masuk, ambang_kata=25)
n = len([b for b in keluar.split('\n') if b.strip()])
cek(f'3 paragraf @30 kata tetap 3 (dapat {n})', n == 3)

print()
print('=== 3. PARAGRAF SANGAT PENDEK MASIH DIGABUNG (jangan hilangkan fungsinya) ===')
pendek = 'Kalimat pendek saja.'
masuk2 = f'{pendek}\n\n{pendek}'
keluar2 = P.merge_short_paragraphs(masuk2, ambang_kata=25)
n2 = len([b for b in keluar2.split('\n') if b.strip()])
cek(f'2 paragraf @3 kata jadi 1 (dapat {n2})', n2 == 1)

print()
print('=== 4. PENANDA & JUDUL TIDAK DIGABUNG ===')
masuk3 = '## BAB 1. Judul\n\n' + ' '.join(['kata'] * 30) + '\n\n[TABEL 1.1: A, B]'
keluar3 = P.merge_short_paragraphs(masuk3, ambang_kata=25)
cek('## BAB tetap sendiri', '## BAB 1. Judul' in keluar3)
cek('[TABEL tetap sendiri', '[TABEL 1.1: A, B]' in keluar3)

print()
print('=== 5. BERGIGI: ambang dikembalikan ke 50 (bug lama) ===')
_lama = P._ambang_paragraf_min
P._ambang_paragraf_min = lambda jenis=None: 50
try:
    keluar4 = P.merge_short_paragraphs(masuk, ambang_kata=None)
    n4 = len([b for b in keluar4.split('\n') if b.strip()])
    cek(f'bug lama tertangkap: 3 paragraf @30 kata jadi {n4} (<3)', n4 < 3,
        'gerbang TIDAK bergigi — bug lama lolos')
finally:
    P._ambang_paragraf_min = _lama

print()
print('=== 6. ANTI-BOCOR: satu baris tak boleh >3000 karakter ===')
besar = '\n\n'.join([' '.join(['kata'] * 30)] * 60)
keluar5 = P.merge_short_paragraphs(besar, ambang_kata=25)
terpanjang = max(len(b) for b in keluar5.split('\n'))
cek(f'paragraf terpanjang {terpanjang} kar < 3000', terpanjang < 3000)

print()
print('=== 7. PEMECAH PARAGRAF PANJANG ADA & BEKERJA (20 Okt 2026) ===')
#  🚨 AKAR: `merge_short_paragraphs` hanya MENGGABUNG, tak pernah MEMECAH.
#  Terukur pada buku baru: AI menulis SATU paragraf 945 kata / 6.565 kar
#  untuk satu sub-bab, dan TIDAK ADA fungsi di jalur penulisan yang memecah.
cek('fungsi pecah_paragraf_panjang ADA',
    hasattr(P, 'pecah_paragraf_panjang'))

#  Suntik paragraf 900 kata (meniru hasil AI nyata).
satu_panjang = ' '.join([f'Kalimat {i} berisi keterangan yang cukup jelas.' 
                         for i in range(1, 101)])
panjang_kar = len(satu_panjang)
h = P.pecah_paragraf_panjang(satu_panjang, ambang_kata=25)
baris_h = [b for b in h.split('\n') if b.strip()]
cek(f'paragraf {panjang_kar} kar DIPECAH jadi {len(baris_h)} bagian',
    len(baris_h) > 3, 'paragraf panjang tidak dipecah')
terp = max(len(b) for b in baris_h)
cek(f'potongan terpanjang {terp} kar < 3000', terp < 3000)

#  Judul & penanda JANGAN dipecah.
campur = '## BAB 1. Judul\n\n' + satu_panjang + '\n\n[TABEL 1.1: A, B]'
h2 = P.pecah_paragraf_panjang(campur, ambang_kata=25)
cek('## BAB tidak dipecah', '## BAB 1. Judul' in h2)
cek('[TABEL tidak dipecah', '[TABEL 1.1: A, B]' in h2)

print()
print('=== 8. URUTAN post_process: PECAH dulu, GABUNG kemudian ===')
import inspect as _insp
src = _insp.getsource(P.post_process)
i_p = src.find('pecah_paragraf_panjang')
i_g = src.find('merge_short_paragraphs')
cek(f'pecah (pos {i_p}) SEBELUM gabung (pos {i_g})',
    0 <= i_p < i_g, 'urutan TERBALIK — paragraf panjang tak akan dipecah')

print()
print('=== 9. JEBAKAN `jenis` TIDAK DITERUSKAN (20 Okt 2026) ===')
#  🚨 TERUKUR: `post_process()` versi pertama memanggil pemecah & penggabung
#  TANPA `jenis` ⇒ keduanya memakai bawaan `umum` (ambang 60) walau buku
#  `anak` (ambang 25). Paragraf 43 kata yang SUDAH dipecah DIGABUNG BALIK
#  jadi 85 kata ⇒ hasil akhir terlihat "tak berubah".
import inspect as _insp2
_src_pp = _insp2.getsource(P.post_process)
cek('post_process meneruskan jenis ke pemecah',
    'pecah_paragraf_panjang(text, jenis=jenis)' in _src_pp,
    'jenis TIDAK diteruskan ke pemecah ⇒ pakai ambang umum')
cek('post_process meneruskan jenis ke penggabung',
    'merge_short_paragraphs(text, jenis=jenis)' in _src_pp,
    'jenis TIDAK diteruskan ke penggabung ⇒ paragraf digabung balik')
cek('tanda tangan post_process punya jenis',
    'jenis' in _insp2.signature(P.post_process).parameters,
    'post_process tidak menerima jenis')
cek('tanda tangan merge punya jenis',
    'jenis' in _insp2.signature(P.merge_short_paragraphs).parameters,
    'merge_short_paragraphs tidak menerima jenis')

#  Uji perilaku: teks 85 kata untuk jenis `anak` HARUS tetap terpecah.
_enam_puluh = ' '.join(['Pagi tadi kami mengamati bayangan di halaman sekolah.'] * 8)
h_anak = P.post_process(_enam_puluh, jenis='anak')
n_anak = len([b for b in h_anak.split('\n') if b.strip()])
cek(f'jenis anak: 8 kalimat → {n_anak} paragraf (harap >1)', n_anak > 1,
    'paragraf digabung balik karena ambang umum dipakai')

print()
print('=' * 60)
print({'lulus': lulus, 'gagal': len(gagal), 'rincian_gagal': gagal})
sys.exit(0 if not gagal else 1)
