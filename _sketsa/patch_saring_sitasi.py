"""Sambungkan penyaring sitasi ke _kalimat_terakhir + _kalimat_pertama."""
import pathlib

p = pathlib.Path('/opt/data/services/eduai-publishing/app/konteks.py')
s = p.read_text()

#  ── _kalimat_terakhir: buang ekor sitasi, ambil kalimat isi terakhir ──
lama_t = """    t = _bersihkan(teks or '')
    if not t:
        return ''
    kal = [k.strip() for k in re.split(r'(?<=[.!?])\\s+', t) if len(k.strip()) > 20]
    if not kal:
        return potong(t, _BATAS_BENANG)
    terakhir = kal[-1]"""
baru_t = """    t = _bersihkan(teks or '')
    if not t:
        return ''
    kal = [k.strip() for k in re.split(r'(?<=[.!?])\\s+', t) if len(k.strip()) > 20]
    if not kal:
        return potong(t, _BATAS_BENANG)
    #  🔴 BUANG ekor sitasi/daftar pustaka (25Sep26): pada naskah nyata benang
    #     masuk terpilih "(Aldo Febriananto Kurniawan, …, 2016)" — bukan
    #     kalimat isi. Ambil kalimat ISI terakhir yang benar-benar kalimat.
    while kal and _kelihatan_sitasi(kal[-1]):
        kal.pop()
    if not kal:
        return ''
    terakhir = kal[-1]"""
assert lama_t in s, 'anchor _kalimat_terakhir tidak ketemu'
s = s.replace(lama_t, baru_t, 1)

print('✅ _kalimat_terakhir: penyaring sitasi dipasang')
p.write_text(s)
