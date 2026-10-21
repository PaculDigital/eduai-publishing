import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/submit_jurnal.py')
s = f.read_text(encoding='utf-8')

# ① ambil volume/nomor/tanggal dari balasan jembatan
lama1 = """        if hasil.get('tautan'):
            a['tautan'] = hasil['tautan']"""
baru1 = """        if hasil.get('tautan'):
            a['tautan'] = hasil['tautan']
        #  ⚠️ 17 Okt 2026: LoA BUTUH Volume + Nomor terbitan dari Tridarma.
        #  Sebelumnya tidak diambil => tombol LoA selalu bilang "belum ada".
        for k in ('volume', 'nomor', 'tanggal_diterima', 'tanggal_terbit',
                  'penulis', 'afiliasi'):
            if hasil.get(k):
                a[k] = hasil[k]"""
assert lama1 in s
s = s.replace(lama1, baru1)
print('✓ ambil volume/nomor dari jembatan')

# ② simpan ikut ke catatan
lama2 = """                    'jurnal': a.get('jurnal') or 'JEMT',
                    'tautan': a.get('tautan') or '',
                    'sumber': 'cek-status'})"""
baru2 = """                    'jurnal': a.get('jurnal') or 'JEMT',
                    'tautan': a.get('tautan') or '',
                    'volume': a.get('volume') or '',
                    'nomor': a.get('nomor') or '',
                    'tanggal_diterima': a.get('tanggal_diterima') or '',
                    'tanggal_terbit': a.get('tanggal_terbit') or '',
                    'penulis': a.get('penulis') or '',
                    'afiliasi': a.get('afiliasi') or '',
                    'sumber': 'cek-status'})"""
assert lama2 in s
s = s.replace(lama2, baru2)
print('✓ simpan volume/nomor ke catatan')

# ③ daftar_artikel juga harus membawa volume/nomor ke layar
lama3 = """                'jurnal': r.get('jurnal') or 'JEMT',
            })"""
baru3 = """                'jurnal': r.get('jurnal') or 'JEMT',
                'volume': r.get('volume') or '',
                'nomor': r.get('nomor') or '',
                'tanggal_diterima': r.get('tanggal_diterima') or '',
            })"""
assert lama3 in s
s = s.replace(lama3, baru3)
print('✓ daftar_artikel bawa volume/nomor')

f.write_text(s, encoding='utf-8')
print('tersimpan')
