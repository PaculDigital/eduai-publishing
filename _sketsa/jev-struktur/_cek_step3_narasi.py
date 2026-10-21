"""CEK: bisakah STEP 3 menyelamatkan naskah disertasi ini?

STEP 3 = KODE ukur KEPADATAN NARASI naskah (nol AI, murah).
Kalau naskah 70% tabel/data -> bukan naskah narasi.
"""
import sys, re
sys.path.insert(0, '/app')
from app import konversi as K
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod
from app.state import buang_daftar_isi

db = SessionLocal()
for fid, lbl in ((75,'Disertasi'), (81,'Asih'), (107,'Unmul'), (78,'TesisS2')):
    fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == fid).first()
    t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
    baris = [' '.join(x.split()) for x in t.split('\n')]
    isi = [b for b in baris if b]
    n_isi = len(isi)
    n_total = len(baris)
    #  --- sinyal 1: kepadatan baris kosong ---
    rasio_kosong = 1 - n_isi / max(1, n_total)
    #  --- sinyal 2: baris kalimat (panjang >=40 kar & berakhir titik) ---
    kal = sum(1 for b in isi if len(b) >= 40 and re.search(r'[.]\s*$', b))
    #  --- sinyal 3: baris sangat pendek (<=25 kar) = tabel/daftar ---
    pendek = sum(1 for b in isi if len(b) <= 25)
    #  --- sinyal 4: baris mengandung angka dominan ---
    angka = sum(1 for b in isi if len(b) > 3 and
                sum(c.isdigit() for c in b)/len(b) > 0.3)
    #  --- sinyal 5: baris berakhir tanda baca kalimat ---
    berakhir = sum(1 for b in isi if re.search(r'[.!?]\s*$', b))
    print(f'═══ {lbl} ({n_total:,} baris, {n_isi:,} berisi) ═══')
    print(f'  baris kosong      : {rasio_kosong*100:5.1f}%')
    print(f'  kalimat utuh(≥40) : {kal*100//max(1,n_isi):5d}%')
    print(f'  SANGAT pendek(≤25): {pendek*100//max(1,n_isi):5d}%')
    print(f'  angka dominan     : {angka*100//max(1,n_isi):5d}%')
    print(f'  berakhir titik    : {berakhir*100//max(1,n_isi):5d}%')
    #  --- VERDICT ---
    narasi = (kal*100//max(1,n_isi))
    print(f'  ⇒ VERDICT: {"NASKAH NARASI" if narasi >= 15 else "BUKAN NARASI (tabel/data)"}')
    print()
db.close()
