"""Uji alur LENGKAP di PRODUKSI: catat LoA uji -> cek lewat domain.
⚠️ Hanya menambah 1 berkas JSON data LoA di bind-mount, TIDAK menyentuh DB user.
"""
import subprocess, json

SKRIP = r'''
import sys, os
sys.path.insert(0, '/app')
from app import loa

s = loa.simpan_setelan({'editor_name': 'Jizenji Tyas Wirastomo',
                        'contact_email': 'admin@tridarma.id',
                        'contact_wa': '0851-7813-8514', 'issue_place': 'Bekasi'})
print('setelan:', s)

# data LoA uji (bukan artikel nyata)
nomor = '1.001'
url = f'https://qr.tridarma.id/verifikasi-loa?no={nomor}'
data = {
    'loa_number': '1.001/LOA/JEMT/X/2026',
    'article_title': 'UJI COBA VERIFIKASI LoA (bukan artikel nyata)',
    'authors': 'Wulan (uji internal)',
    'affiliation': 'Tridarma Journal Publishing',
    'submission_id': 'UJI-001',
    'acceptance_date': '17 Oktober 2026',
    'volume': '1', 'issue': '2', 'publication_date': 'Desember 2026',
    'editor_name': 'Jizenji Tyas Wirastomo',
    'verify_url': url,
}
loa.catat_terbit(nomor, data)
print('LoA uji dicatat:', nomor)
print('cek balik:', bool(loa.cek_nomor(nomor)))
'''
r = subprocess.run(['docker', 'exec', '-i', 'eduai-app', 'python3', '-'],
                   input=SKRIP, capture_output=True, text=True, timeout=120)
print(r.stdout)
if r.stderr.strip():
    print('STDERR:', r.stderr.strip()[:600])
