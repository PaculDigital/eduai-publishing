"""Bikin berkas HTML uji tampilan ikon aksi — DIPERBAIKI 24Sep26.

⚠️ CACAT ALAT UKUR YANG DITUTUP (temuan MATA, bukan uji teks):
   Berkas uji versi pertama mengambil isi <symbol> dengan cara
   `spr[i:j].split('>',1)[1]` → ATRIBUT viewBox TERBUANG, sehingga ikon
   digambar dengan koordinat salah = tampak sebagai artefak/segitiga hitam,
   dan ikon `x` tidak muncul sama sekali.
   Pelajaran: alat ukur bisa berbohong. Kalau hasil tak sesuai harapan,
   SADARI ALAT UKUR SENDIRI DULU (aturan Bos 24Sep26).

⚠️ CACAT KE-2: CSS diambil dari `.kb-log-lencana.lewat` sampai `.kb-log-buka`
   → definisi `.selesai` (hijau) & `.hilang` TIDAK IKUT → lencana "Sudah oke"
   tampil tanpa warna. Obat: ambil SEMUA baris `.kb-log-lencana`.
"""
import re, sys, os

BASE = '/opt/data/services/eduai-publishing'
src = open(f'{BASE}/app/templates/naskah.html').read()

#  ── CSS: SEMUA aturan lencana + seluruh blok ikon aksi ──────────────
css_lencana = '\n'.join(re.findall(r'^\.kb-log-lencana[^\n]*\n?', src, re.M))
a = src.index('/*  ═══ IKON AKSI CATATAN')
b = src.index('.kb-log-buka')
css_ikon = src[a:b]
#  Tooltip & keadaan mati ikut (letaknya setelah .kb-log-buka).
c = src.index('/*  Tooltip kotak gelap')
d = src.index('@media(max-width:420px){\n  .kb-ik')
css_tip = src[c:d]
e = src.index('@media(max-width:420px){\n  .kb-ik')
f = src.index('.kb-log-buka', e)
css_media = src[e:f]

#  ── IKON: ambil <symbol> UTUH (viewBox ikut) ────────────────────────
spr = open(f'{BASE}/app/static/ikon/lucide.svg').read()
symbols = ''
for nama in ('sparkles', 'pencil', 'x'):
    j = spr.index(f'id="ik-{nama}"')
    i = spr.rindex('<symbol', 0, j)          # mulai dari '<symbol' — bukan
    k = spr.index('</symbol>', j) + len('</symbol>')   # dari 'id=' (cacat!)
    symbols += spr[i:k] + '\n'

HTML = f"""<!DOCTYPE html><html lang=id><head><meta charset=utf-8>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;background:#F6F7F5;
  margin:0;padding:22px;color:#22301F}}
.kb-log-baris{{display:flex;gap:11px;align-items:flex-start;background:#fff;
  border:1px solid #E4E7E4;border-radius:12px;padding:13px 15px;margin-bottom:10px}}
.kb-log-nomor{{width:22px;height:22px;border-radius:50%;background:#EFF1EE;
  color:#5A6A57;font-size:12px;font-weight:700;display:flex;align-items:center;
  justify-content:center;flex:none;margin-top:2px}}
.kb-log-teks{{flex:1;min-width:0}}
.kb-log-teks .isi{{font-size:14px;line-height:1.5}}
.kb-log-teks .bagian{{font-size:11.5px;color:#7A8577;margin-top:3px}}
{css_lencana}
{css_ikon}
{css_tip}
{css_media}
svg.ik{{display:block}}
</style></head><body>
<svg width="0" height="0" style="position:absolute">
{symbols}
</svg>
<div style="font-size:13px;font-weight:700;margin-bottom:12px">
Log Revisi — Pembimbing · 3 catatan</div>
"""


def baris(no, isi, bagian, lencana, kelas, mati='', hover=False):
    h = ' hover' if hover else ''
    return f"""<div class="kb-log-baris">
  <div class="kb-log-nomor">{no}</div>
  <div class="kb-log-teks"><div class="isi">{isi}</div>
    <div class="bagian">{bagian}</div></div>
  <div class="kb-aksi">
    <button class="kb-ik ai{mati}{h}" data-tip="Revisi dengan AI">
      <svg class="ik" width="16" height="16" aria-hidden="true">
        <use href="#ik-sparkles"></use></svg></button>
    <button class="kb-ik manual{mati}" data-tip="Dikerjakan sendiri">
      <svg class="ik" width="15" height="15" aria-hidden="true">
        <use href="#ik-pencil"></use></svg></button>
    <button class="kb-ik lewat{mati}" data-tip="Lewati revisi ini">
      <svg class="ik" width="15" height="15" aria-hidden="true">
        <use href="#ik-x"></use></svg></button>
  </div>
  <div class="kb-log-lencana {kelas}">{lencana}</div>
</div>"""


HTML += baris(1, 'Latar belakang belum menunjukkan kesenjangan penelitian.',
              'BAB I · 1.1 Latar Belakang', 'Belum selesai', '',
              hover=True)
HTML += baris(2, 'Tambahkan data BPS terbaru.',
              'BAB I · 1.1 Latar Belakang', 'Revisi Dilewati', 'lewat',
              mati=' kb-mati')
HTML += baris(3, 'Tabel 4.2 belum ada sumbernya.',
              'BAB IV · 4.2 Hasil', 'Sudah oke', 'selesai')
HTML += '</body></html>'

out = '/tmp/uji_ikon_aksi.html'
open(out, 'w').write(HTML)
print(f'✓ {out} ({os.path.getsize(out)} byte)')
print(f'  CSS lencana : {len(css_lencana)} kar ({css_lencana.count(chr(10))} baris)')
print(f'  CSS ikon    : {len(css_ikon)} kar')
print(f'  symbol      : {symbols.count("<symbol")} buah, viewBox ikut: '
      f'{"viewBox" in symbols}')
