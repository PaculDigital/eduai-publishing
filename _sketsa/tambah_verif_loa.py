import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/loa.py')
s = f.read_text(encoding='utf-8')

TAMBAHAN = '''

# ══════════════════════════════════════════════════════════════════════════
#  DAFTAR LoA TERBIT + VERIFIKASI  (halaman qr.tridarma.id)
# ══════════════════════════════════════════════════════════════════════════
BERKAS_TERBIT = DIR_DATA / 'loa-terbit.json'


def _muat_terbit() -> dict:
    """Baca daftar LoA yang sudah terbit (kunci = nomor LoA pendek, mis. '1.001')."""
    try:
        if BERKAS_TERBIT.exists():
            isi = json.loads(BERKAS_TERBIT.read_text(encoding='utf-8'))
            if isinstance(isi, dict):
                return isi
    except Exception:
        pass
    return {}


def catat_terbit(nomor: str, data: dict) -> None:
    """Simpan LoA yang baru dicetak supaya bisa diverifikasi publik."""
    isi = _muat_terbit()
    isi[str(nomor)] = {
        'nomor': str(nomor),
        'nomor_surat': data.get('loa_number') or '',
        'judul': data.get('article_title') or '',
        'penulis': data.get('authors') or '',
        'afiliasi': data.get('affiliation') or '',
        'id_ojs': data.get('submission_id') or '',
        'tanggal_diterima': data.get('acceptance_date') or '',
        'terbit': _ringkas_terbit(data),
        'editor': data.get('editor_name') or '',
        'diterbitkan_pada': datetime.now().strftime('%d %B %Y').replace(
            'January', 'Januari').replace('February', 'Februari').replace(
            'March', 'Maret').replace('May', 'Mei').replace('June', 'Juni').replace(
            'July', 'Juli').replace('August', 'Agustus').replace(
            'October', 'Oktober').replace('December', 'Desember'),
    }
    BERKAS_TERBIT.parent.mkdir(parents=True, exist_ok=True)
    BERKAS_TERBIT.write_text(json.dumps(isi, indent=1, ensure_ascii=False),
                             encoding='utf-8')


def _ringkas_terbit(data: dict) -> str:
    vol = str(data.get('volume') or '').strip()
    no = str(data.get('issue') or '').strip()
    tgl = str(data.get('publication_date') or '').strip()
    bagian = [b for b in (f'Volume {vol}' if vol else '',
                          f'Nomor {no}' if no else '') if b]
    inti = ', '.join(bagian)
    return f'{inti} — {tgl}' if (inti and tgl) else (inti or tgl)


def cek_nomor(nomor: str) -> dict:
    """Cari LoA berdasarkan nomor (terima '1.001' atau nomor surat lengkap)."""
    n = (nomor or '').strip()
    if not n:
        return {}
    isi = _muat_terbit()
    if n in isi:
        return isi[n]
    # cocokkan juga kalau user mengetik nomor surat lengkap (1.001/LOA/JEMT/X/2026)
    for _, d in isi.items():
        if d.get('nomor_surat') and d['nomor_surat'].lower() == n.lower():
            return d
    return {}
'''

if 'def cek_nomor' not in s:
    s = s.rstrip('\n') + '\n' + TAMBAHAN
    f.write_text(s, encoding='utf-8')
    print('✓ 3 fungsi ditambahkan: catat_terbit, cek_nomor, _ringkas_terbit')
else:
    print('sudah ada')

import re
print('fungsi di loa.py:', re.findall(r'^def (\w+)', s, re.M))
