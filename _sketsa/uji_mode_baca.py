"""UJI 3 HAL — Mode Baca OnlyOffice (perintah Bos 02Okt26).

Dijalankan SEBELUM mengkode Pembimbing AI. Tujuan: MENJAWAB 3 pertanyaan
dengan BUKTI, bukan tebakan.

  1. Mode baca: tombol benar-benar MATI?
  2. Komentar & sorotan masih bisa dipakai di mode baca?
  3. Pagar simpan memblokir di SERVER, bukan cuma tampilan?

CARA: panggil konfigurasi_editor() LANGSUNG di dalam container (tanpa menyentuh
produksi, tanpa deploy, tanpa mengubah berkas apa pun).

JALANKAN:  docker exec eduai-app python3 /app/_sketsa/uji_mode_baca.py
           (salin dulu: docker cp _sketsa/uji_mode_baca.py eduai-app:/app/_sketsa/)
"""
from __future__ import annotations

import json

from app import onlyoffice

LAPOR = []


def catat(no: int, judul: str, hasil: str, bukti: str = ''):
    LAPOR.append({'no': no, 'judul': judul, 'hasil': hasil, 'bukti': bukti})
    print(f'[{hasil}] {no}. {judul}')
    if bukti:
        print(f'      bukti: {bukti}')


# ═══════════════════════════════════════════════════════════════════
#  BAGIAN A — apa yang DIKIRIM ke OnlyOffice untuk tiap mode
# ═══════════════════════════════════════════════════════════════════
print('=' * 70)
print('BAGIAN A — CONFIG EDITOR: mode "edit" vs mode "view"')
print('=' * 70)

umum = dict(
    kunci='e99v1', nama='uji.docx',
    url_unduh='https://contoh/unduh/tok',
    url_simpan='https://contoh/simpan/tok',
    user_id=1, user_nama='Uji', extensi='.docx',
)

cfg_edit = onlyoffice.konfigurasi_editor(**umum)

# mode view: paksa lewat modul — cari cara yang didukung
cfg_view = None
try:
    # coba parameter mode manual kalau ada
    cfg_view = onlyoffice.konfigurasi_editor(**{**umum, 'mode': 'view'})
except TypeError:
    # tidak ada parameter mode → panggil langsung fungsi tipe_dokumen
    print('  (konfigurasi_editor tidak punya parameter `mode` — dibuat manual)')
    cfg_view = json.loads(json.dumps(cfg_edit))     # salin
    cfg_view.setdefault('document', {})
    cfg_view['document']['permissions'] = {
        'edit': False, 'comment': False, 'download': True,
    }
    cfg_view['editorConfig'] = cfg_view.get('editorConfig', {})
    cfg_view['editorConfig']['mode'] = 'view'

print()
print('── A1. permissions mode EDIT ──')
print(json.dumps(cfg_edit['document']['permissions'], indent=2, ensure_ascii=False))
per_edit = cfg_edit['document']['permissions']
catat(1, 'mode edit: izin "edit" hidup?',
      'YA' if per_edit.get('edit') else 'TIDAK',
      f"edit={per_edit.get('edit')}, comment={per_edit.get('comment')}")

print()
print('── A2. permissions mode VIEW ──')
print(json.dumps(cfg_view['document']['permissions'], indent=2, ensure_ascii=False))
per_view = cfg_view['document']['permissions']
catat(2, 'mode view (permissions.edit=False, comment=False): semua izin mati?',
      'YA' if not any([per_view.get('edit'), per_view.get('comment'),
                       per_view.get('fillForms'), per_view.get('modifyFilter')])
      else 'TIDAK',
      json.dumps(per_view, ensure_ascii=False))

print()
print('── A3. Bagaimana menyalakan KOMENTAR sambil mematikan TULIS? ──')
kombinasi = {
    'edit': False, 'comment': True, 'download': True,
    'fillForms': False, 'modifyFilter': False, 'modifyContentControl': False,
}
print(json.dumps(kombinasi, indent=2, ensure_ascii=False))
catat(3, 'kombinasi "baca + komentar" (edit=False, comment=True) didukung OO?',
      'PERLU UJI DI LAYAR',
      'permissions di atas = dugaan; wajib dibuktikan dengan MATA di editor')

print()
print('── A4. Apakah url_simpan selalu dikirim? ──')
kirim_simpan = cfg_edit['editorConfig'].get('callbackUrl') or \
    cfg_edit.get('callbackUrl') or '(lihat cfg penuh)'
print(f'  callbackUrl: {kirim_simpan}')
catat(4, 'config editor selalu memuat callbackUrl (url_simpan)?',
      'YA' if kirim_simpan != '(lihat cfg penuh)' else 'CEK MANUAL',
      str(kirim_simpan)[:80])

print()
print('── A5. Struktur cfg penuh (kunci utama) ──')
print('  kunci cfg     :', sorted(cfg_edit.keys()))
print('  documentType  :', cfg_edit.get('documentType'))
print('  document.kunci:', sorted(cfg_edit.get('document', {}).keys()))
print('  editorConfig  :', sorted(cfg_edit.get('editorConfig', {}).keys()))

print()
print('=' * 70)
print('BAGIAN B — PAGAR SIMPAN: apakah menolak token BUKAN pemilik?')
print('=' * 70)

from app.main import _token_berkas

tok_pemilik = _token_berkas(80, 7)        # (berkas 80, user 7) = pemilik
tok_lain = _token_berkas(80, 999)         # (berkas 80, user 999) = BUKAN pemilik

print(f'  token pemilik (fid=80, uid=7)   : {tok_pemilik}')
print(f'  token pembaca (fid=80, uid=999) : {tok_lain}')
print(f'  dua token BERBEDA?              : {tok_pemilik != tok_lain}')
catat(5, 'token pembaca TIDAK akan cocok di pagar simpan (yg cek pemilik)',
      'YA' if tok_pemilik != tok_lain else 'TIDAK',
      'pagar: if _token_berkas(fb.id, fb.user_id) == token → hanya pemilik')

print()
print('=' * 70)
print('RINGKASAN')
print('=' * 70)
for r in LAPOR:
    print(f"  [{r['hasil']:<18}] {r['no']}. {r['judul']}")
print()
print('CATATAN: bagian A & B = bukti DARI DALAM mesin (kode/config).')
print('Untuk pertanyaan 1 & 2 (tombol mati + komentar) WAJIB dibuktikan')
print('dengan MATA di editor sungguhan — lanjut skrip uji layar.')
