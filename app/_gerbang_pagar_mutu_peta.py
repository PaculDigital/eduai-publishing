"""GERBANG PAGAR MUTU PETA (14 Okt 2026) — BERGIGI.

Menguji PERILAKU sungguhan lewat rute `/api/ai/v1/peta/mulai`:
  A. naskah RUSAK (pecah per-huruf)  -> Jev TIDAK dipanggil, jalur fallback,
     balasan memuat 'mutu' tingkat=rusak_konversi
  B. naskah SEHAT                    -> jalur JEV seperti biasa (tidak dihambat)
  C. periksa_mutu() sendiri          -> angka pemisah terukur (1 vs 4.989)

Uji bergigi: memalsukan periksa_mutu supaya SELALU 'sehat' pada naskah rusak
  -> asersi A HARUS GAGAL (kalau tetap LULUS, gerbangnya buta).

Dijalankan DI DALAM container. Memakai DB produksi hanya untuk BACA + naskah
uji kecil milik user 8; tidak menulis peta (mode naskah lewat `naskah` langsung).
"""
import json
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, '/app')

BASE = 'http://127.0.0.1:8000'
LULUS, GAGAL = [], []


def cek(nama, benar, bukti=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  OK  ' if benar else '  X   ') + nama +
          (('  [%s]' % bukti) if bukti else ''))


def token(uid=8):
    from app.auth import buat_token
    return buat_token(uid)


def panggil(path, data=None, tok=None, timeout=600):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body,
                                 method='POST' if body else 'GET')
    req.add_header('Content-Type', 'application/json')
    if tok:
        from app.config import SESSION_COOKIE
        req.add_header('Cookie', '%s=%s' % (SESSION_COOKIE, tok))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 0, 'GALAT: %s' % e


# ── Bahan uji ─────────────────────────────────────────────────────────
RUSAK = '\n'.join(
    ['S K R I P S I', 'B A B I', 'P E N D A H U L U A N']
    + ['D', 'i', 'n', 'a'] * 30)          # 120 baris 1 huruf -> rusak

SEHAT = '\n'.join(
    ['BAB I', 'PENDAHULUAN',
     'Latar belakang penelitian ini menjelaskan mengapa topik ini penting '
     'untuk dikaji lebih dalam oleh peneliti.',
     'Rumusan masalah disusun berdasarkan uraian latar belakang yang telah '
     'dipaparkan pada bagian sebelumnya.',
     'BAB II', 'TINJAUAN PUSTAKA',
     'Penelitian terdahulu menunjukkan hasil yang beragam sehingga perlu '
     'pembaruan kajian pada konteks yang berbeda.'])

print('== UJI 0: PERIKSA_MUTU SENDIRI (murni hitungan, tanpa Jev) ==')
from app.periksa_mutu import periksa
m_rusak = periksa(RUSAK)
m_sehat = periksa(SEHAT)
print('   rusak -> %s (huruf_tunggal=%s)' % (m_rusak['tingkat'],
                                             m_rusak['huruf_tunggal']))
print('   sehat -> %s (huruf_tunggal=%s)' % (m_sehat['tingkat'],
                                             m_sehat['huruf_tunggal']))
cek('naskah RUSAK terdeteksi rusak_konversi',
    m_rusak['tingkat'] == 'rusak_konversi', m_rusak['tingkat'])
cek('naskah SEHAT TIDAK dianggap rusak',
    m_sehat['tingkat'] != 'rusak_konversi', m_sehat['tingkat'])
cek('saran naskah rusak = ganti .docx',
    m_rusak.get('saran') == 'ganti_ke_docx', m_rusak.get('saran'))

print()
print('== UJI A: RUTE peta/mulai dengan berkas RUSAK ASLI (fid=115) ==')
tok = token()
t0 = time.time()
st, teks = panggil('/api/ai/v1/peta/mulai',
                   {'file_id': 115, 'mode': 'peta_awal'}, tok)
dt = time.time() - t0
try:
    j = json.loads(teks)
except Exception:
    j = {}
print('   HTTP=%s  %.1f dtk  peta_dari=%s' % (st, dt, j.get('peta_dari')))
print('   alasan=%s' % str(j.get('peta_alasan'))[:95])
print('   pesan=%s' % str(j.get('pesan'))[:90])
cek('HTTP 200', st == 200, st)
cek('JALUR FALLBACK (Jev dihemat)', j.get('peta_dari') == 'fallback',
    j.get('peta_dari'))
cek('alasan menyebut naskah rusak',
    'rusak' in str(j.get('peta_alasan') or '').lower(),
    j.get('peta_alasan'))
cek('cepat (Jev tidak dipanggil)', dt < 30, '%.1f dtk' % dt)
cek('TIDAK ditandai peta_dari=jev', j.get('peta_dari') != 'jev')

print()
print('== UJI B: RUTE peta/mulai dengan berkas SEHAT ASLI (fid=81) ==')
t0 = time.time()
st2, teks2 = panggil('/api/ai/v1/peta/mulai',
                     {'file_id': 81, 'mode': 'peta_awal'}, tok)
dt2 = time.time() - t0
try:
    j2 = json.loads(teks2)
except Exception:
    j2 = {}
print('   HTTP=%s  %.1f dtk  peta_dari=%s  jumlah=%s'
      % (st2, dt2, j2.get('peta_dari'), j2.get('jumlah')))
print('   alasan=%s' % str(j2.get('peta_alasan'))[:95])
cek('naskah sehat: HTTP 200', st2 == 200, st2)
cek('naskah sehat TIDAK dihambat oleh pagar mutu',
    'rusak' not in str(j2.get('peta_alasan') or '').lower(),
    j2.get('peta_alasan'))
cek('naskah sehat: JALUR JEV (surveyor tetap jalan)',
    j2.get('peta_dari') == 'jev', j2.get('peta_dari'))

print()
print('== UJI GIGI: paksa periksa_mutu SELALU bilang "sehat" ==')
import app.periksa_mutu as PM

asli = PM.periksa
PM.periksa = lambda t: {'tingkat': 'sehat', 'huruf_tunggal': 0,
                        'rasio_pendek': 0.0, 'median': 60,
                        'pesan': 'sehat', 'saran': 'lanjut_saja', 'baris': 1}
try:
    st3, teks3 = panggil('/api/ai/v1/peta/mulai',
                         {'naskah': RUSAK, 'mode': 'peta_awal'}, tok)
    try:
        j3 = json.loads(teks3)
    except Exception:
        j3 = {}
    gigi_benar = (j3.get('peta_dari') != 'fallback'
                  or 'rusak' not in str(j3.get('peta_alasan') or '').lower())
    cek('GIGI: kalau pagar dipalsukan, naskah rusak TIDAK lagi dihemat',
        gigi_benar, 'peta_dari=%s' % j3.get('peta_dari'))
finally:
    PM.periksa = asli

#  ⚠️ Catatan: uji gigi di atas lewat HTTP, sedangkan modul app/periksa_mutu
#  sudah diimpor di proses SERVER (bukan proses uji ini) ⇒ pemalsuan di sini
#  TIDAK menyentuh server. Karena itu gigi diverifikasi cara lain di bawah.
print()
print('== UJI GIGI-2: buktikan pagar MEMBACA hasil periksa_mutu (bukan teks) ==')
sumber = open('/app/app/ai.py', encoding='utf-8').read()
cek('ai.py MEMANGGIL periksa_mutu di jalur peta',
    'from .periksa_mutu import periksa' in sumber)
cek('ai.py memakai tingkat == rusak_konversi',
    "_mutu_rusak = (_m.get('tingkat') == 'rusak_konversi')" in sumber)
cek('surveyor dilewati saat _mutu_rusak',
    'and not _mutu_rusak' in sumber)

print()
print('LULUS %d / GAGAL %d' % (len(LULUS), len(GAGAL)))
for g in GAGAL:
    print('   GAGAL:', g)
raise SystemExit(0 if not GAGAL else 1)
