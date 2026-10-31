"""Uji Kata Pengantar spesifik + nada referensi (paket sempurna, Gas
Bos 31 Okt 2026 malam, item 4). Jalankan dari root checkout:
python3 uji_pengantar.py
Tidak menyentuh DB produksi, tidak memanggil API nyata, tidak memakai
LLM nyata: jalur LLM diuji dengan modul palsu di sys.modules.
Memakai fungsi ASLI dari buku_umum_assembly.
"""

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import buku_umum_assembly as A
from docx import Document

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s %s' % (nama, bukti))


BAB5 = """### 5.1 Definisi
Isi definisi yang panjang, bukan tesis.
### 5.4 Posisi dan Sintesis Penulis
Posisi penulis: transformasi digital hanya menaikkan kinerja UMKM bila
dimediasi transformasi proses bisnis, dengan kapasitas serap sebagai
prasyarat dan tiga dimensi nilai sebagai ukuran keberhasilan.
Argumen ini dirangkai dari seluruh bab dan menjadi tesis buku ini.
### 5.5 Implikasi
Implikasi praktis dibahas di sini, bukan tesis.
### Ringkasan Bab
Ringkasan penutup bab lima."""

tesis = A._tesis_bab_akhir(BAB5)
cek('ekstraksi-tesis-5.4', 'transformasi proses bisnis' in tesis
    and 'Implikasi praktis' not in tesis, tesis[:80])
cek('ekstraksi-tanpa-5.4-kosong',
    A._tesis_bab_akhir('### 5.1 Definisi\nIsi saja.') == '')


def paras(doc):
    return [p.text for p in doc.paragraphs if p.text.strip()]


# Jalur LLM: modul palsu di sys.modules, prompt dicatat.
catat = {}


def llm_palsu(prompt, max_tokens=1500, timeout=120):
    catat['prompt'] = prompt
    return ('Pertanyaan utama buku ini adalah bagaimana transformasi '
            'digital benar-benar bekerja pada UMKM, bukan sekadar '
            'diadopsi sebagai perangkat baru yang dipasang tanpa mengubah '
            'cara kerja.\n\n'
            'Posisi penulis menegaskan mediasi transformasi proses '
            'bisnis sebagai syarat kinerja, dengan kapasitas serap '
            'sebagai prasyarat dan tiga dimensi nilai sebagai ukuran '
            'keberhasilan yang dapat dievaluasi.\n\n'
            'Buku ini ditujukan bagi mahasiswa, peneliti, dan pelaku '
            'UMKM yang membutuhkan kerangka evaluasi berbasis bukti '
            'untuk menilai program digitalisasi secara jujur.')


palsu = types.ModuleType('buku_umum_pipeline')
palsu.call_llm = llm_palsu
sys.modules['buku_umum_pipeline'] = palsu
doc = Document()
A.add_kata_pengantar(doc, 'Transformasi Digital UMKM', 'Uji Buku',
                      'Institusi Uji',
                      bab_akhir_teks=BAB5,
                      struktur_bab=['Lanskap', 'Strategi', 'Adopsi',
                                    'Dampak', 'Sintesis'])
teks = '\n'.join(paras(doc))
cek('pengantar-llm-spesifik', 'transformasi proses bisnis' in teks
    and 'disusun mengalir' not in teks, teks[:120])
cek('prompt-memuat-tesis-dan-struktur',
    'transformasi proses bisnis' in catat.get('prompt', '')
    and 'Sintesis' in catat.get('prompt', ''), catat.get('prompt', '')[:80])
del sys.modules['buku_umum_pipeline']

# Fallback: tanpa teks bab akhir -> templat lama.
doc2 = Document()
A.add_kata_pengantar(doc2, 'Transformasi Digital UMKM', 'Uji Buku',
                      'Institusi Uji')
teks2 = '\n'.join(paras(doc2))
cek('fallback-templat-tanpa-bab', 'disusun mengalir' in teks2,
    teks2[:120])


# Fallback: LLM gagal -> templat lama.
def llm_gagal(prompt, max_tokens=1500, timeout=120):
    raise RuntimeError('provider down')


palsu2 = types.ModuleType('buku_umum_pipeline')
palsu2.call_llm = llm_gagal
sys.modules['buku_umum_pipeline'] = palsu2
doc3 = Document()
A.add_kata_pengantar(doc3, 'Transformasi Digital UMKM', 'Uji Buku',
                      'Institusi Uji', bab_akhir_teks=BAB5,
                      struktur_bab=['Lanskap', 'Sintesis'])
teks3 = '\n'.join(paras(doc3))
cek('fallback-templat-llm-gagal', 'disusun mengalir' in teks3,
    teks3[:120])
del sys.modules['buku_umum_pipeline']

print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
