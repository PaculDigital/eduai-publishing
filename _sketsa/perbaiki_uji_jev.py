import pathlib

p = pathlib.Path('/opt/data/services/eduai-publishing/_uji_jev_nilai_balasan.py')
s = p.read_text()

LAMA = '''def _balasan(choice: str, conf: float) -> str:
    """Bentuk balasan 9router (stream) yang berisi answers jev."""
    isi = json.dumps({'answers': {'ngawur': {'choice': choice,
                                             'confidence': conf,
                                             'noul': 'test'}}})
    return json.dumps({'choices': [{'message': {'content': isi}}]})'''

BARU = '''def _balasan(choice: str, conf: float, sesuai: str = 'ya',
             sisip: str = 'tidak') -> str:
    """Bentuk balasan 9router yang berisi 3 jawaban jev.

    Jejak uji 05Okt26: uji pertama hanya mengisi 'ngawur', padahal jev
    SUNGGUHAN menjawab 3 pertanyaan sekaligus — uji harus menirukan ketiganya.
    """
    isi = json.dumps({'answers': {
        'ngawur': {'choice': choice, 'confidence': conf, 'noul': 'test'},
        'sesuai_tugas': {'choice': sesuai, 'confidence': 0.9, 'noul': 'test'},
        'menyisipkan': {'choice': sisip, 'confidence': 0.9, 'noul': 'test'},
    }})
    return json.dumps({'choices': [{'message': {'content': isi}}]})'''

print('ganti _balasan:', LAMA in s)
s = s.replace(LAMA, BARU)

TAMBAH_LAMA = """    ('jev: pilihan tak dikenal → TOLAK (P7)',
     _balasan('entahlah', 0.99), False, 8.0, 336, 'tolak'),
]"""
TAMBAH_BARU = """    ('jev: pilihan tak dikenal → TOLAK (P7)',
     _balasan('entahlah', 0.99), False, 8.0, 336, 'tolak'),
    ('jev: WAJAR tapi TIDAK sesuai tugas → TOLAK',
     _balasan('tidak_sah_wajar', 0.95, sesuai='tidak'), False, 8.0, 336, 'tolak'),
    ('jev: WAJAR tapi MENYISIPKAN bagian baru → TOLAK',
     _balasan('tidak_sah_wajar', 0.95, sisip='ya'), False, 8.0, 336, 'tolak'),
]"""
print('tambah kasus:', TAMBAH_LAMA in s)
s = s.replace(TAMBAH_LAMA, TAMBAH_BARU)

p.write_text(s)
print('selesai')
