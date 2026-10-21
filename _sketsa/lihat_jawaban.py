import os, sys, tempfile
from pathlib import Path
os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='lihat_')
sys.path.insert(0,'/app')
import asyncio
from app import ai as A, state as S, konteks as K, gambar as G

F = Path('/app/uploads/6/349508cb13697288.docx')
t = A._teks_dari_berkas(F, F.name)
peta = S.petakan(S.buang_daftar_isi(t))
target = '2.3'
i = next(k for k,x in enumerate(peta) if str(x.get('section_id'))==target)

print('── BENANG MASUK (kalimat terakhir 2.2) ──')
print('  ', S.__dict__.get('_x') or K._kalimat_terakhir(peta[i-1].get('isi_teks','')))
print()
print('── BENANG KELUAR (kalimat pertama 2.4) ──')
print('  ', K._kalimat_pertama(peta[i+1].get('isi_teks','')))
print()
km = ('Tambahkan grafik pertumbuhan jumlah peserta latihan per tahun: '
      '2020=120, 2021=180, 2022=240, 2023=310, 2024=395.')
pr = K.bangun_prompt(bagian_target=target, peta=peta,
                     isi_saat_ini=peta[i].get('isi_teks',''), komentar=km)
msg,info = asyncio.run(A._panggil_9router(pr+'\n\n=== PERMINTAAN USER ===\n'+km, 900))
print('── JAWABAN AI (utuh) ──')
print(msg)
