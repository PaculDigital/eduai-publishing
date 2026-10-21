"""UJI LAYAR 3d — elemen Done (Tiket Lolos) di halaman konversi.

Keadaan:
  ① ada tiket 'gap' → 'Gap' tampil Done + TIDAK punya checkbox
  ② elemen tanpa tiket → tetap punya checkbox (bisa dibeli)
  ③ uji gigi: daftar_revisi tanpa tiket → TIDAK ada Done
"""
import os
import sys

os.makedirs("/tmp/uji3d", exist_ok=True)
sys.path.insert(0, "/app")

from app import main as M                       # noqa: E402
from app import konversi as K                   # noqa: E402
from app import tiket_lolos as T                # noqa: E402

lulus, gagal = [], []


def cek(nama, syarat, bukti=""):
    (lulus if syarat else gagal).append(nama)
    print(f"  {'✅' if syarat else '❌'} {nama}" + (f"  → {bukti}" if bukti else ""))


ARTIKEL = {'judul': 'Uji', 'abstrak_id': 'x',
           'elemen': {'gap': 'isi gap', 'novelty': 'isi novelty',
                      'hook': 'isi hook'}}

# ── 1. TANPA tiket → semua punya checkbox, nol Done ──────────────────
print("\n══ 1. TANPA tiket → tidak ada Done ══")
d1 = K.daftar_revisi(ARTIKEL, None)
done1 = [i['label'] for i in d1 if i['done']]
cek("1a nol elemen Done", done1 == [], str(done1))
gap1 = [i for i in d1 if i['kunci'] == 'elemen:gap'][0]
cek("1b 'Gap' done=False", gap1['done'] is False, str(gap1['done']))

# ── 2. ADA tiket 'gap' → 'Gap' Done ─────────────────────────────────
print("\n══ 2. tiket 'gap' ada → 'Gap' Done ══")
d2 = K.daftar_revisi(ARTIKEL, {'gap': {'bab': 'Pendahuluan ¶4', 'sidik': 'x'}})
gap2 = [i for i in d2 if i['kunci'] == 'elemen:gap'][0]
nov2 = [i for i in d2 if i['kunci'] == 'elemen:novelty'][0]
cek("2a 'Gap' done=True", gap2['done'] is True, str(gap2['done']))
cek("2b 'Novelty' tetap done=False", nov2['done'] is False, str(nov2['done']))
cek("2c 'Gap' harga TETAP ada (3 token, tidak hilang)",
    gap2['token'] == 3, str(gap2['token']))

# ── 3. BAGIAN artikel TIDAK Pernah Done ─────────────────────────────
print("\n══ 3. bagian artikel (abstrak dll) tidak dapat Done ══")
abstrak = [i for i in d2 if i['kunci'] == 'abstrak_id']
if abstrak:
    cek("3a bagian artikel done=False", abstrak[0]['done'] is False,
        str(abstrak[0]['done']))

# ── 4. UJI GIGI: fungsi daftar_revisi diuji 2 bentuk ────────────────
print("\n══ 4. UJI GIGI: bentuk lama (tanpa argumen tiket) tetap jalan ══")
d4 = K.daftar_revisi(ARTIKEL)
cek("4a bentuk lama tidak error", len(d4) > 0, str(len(d4)))
cek("4b 'done' ada di semua item", all('done' in i for i in d4))

# ── 5. LAYAR NYATA: halaman konversi menampilkan Done ───────────────
print("\n══ 5. LAYAR NYATA (template sungguhan) ══")
from app.models import KonversiNaskah, User          # noqa: E402
import json as _json                                # noqa: E402

db = M.SessionLocal()
u = db.query(User).filter(User.email == 'asih.susanti@eduai.test').first()
FID = 81
db.query(KonversiNaskah).filter(KonversiNaskah.user_id == u.id,
                                KonversiNaskah.file_id == FID).delete()
db.commit()
db.add(KonversiNaskah(user_id=u.id, file_id=FID, status='beres',
                      hasil_json=_json.dumps({
                          'artikel': ARTIKEL,
                          'tiket': {'gap': {'bab': 'Pendahuluan ¶4',
                                            'sidik': 'x' * 100}}})))
db.commit()

tpl = M.templates.get_template('artikel_konversi.html')
html = tpl.render({
    'request': None, 'user': u, 'berkas': None, 'naskah_ada': True,
    'siap': {'boleh': True, 'pesan': '', 'henti': False,
             'identitas': {'nama': 'Asih', 'email': 'a@b.c'},
             'kelengkapan': {'kurang': []}, 'mutu': {'kurang': []},
             'jenis': {'jenis': 'jurnal', 'yakin': 0.9},
             'mata': {}, 'bentuk': None},
    'jenis': {'jenis': 'jurnal', 'yakin': 0.9},
    'mutu': {'kurang': []}, 'mutu_pesan': '', 'jatah': {'sisa': 3, 'maks': 3},
    'token_per_revisi': 2, 'label_jenis': {},
    'artikel_ada': True,
    'daftar_revisi': K.daftar_revisi(ARTIKEL,
                                     {'gap': {'bab': 'P', 'sidik': 'x'}}),
    'saldo_revisi': 10, 'biaya_revisi': {'per_item': {}, 'total': 0},
    'tiket': {'lolos': ['Gap (celah penelitian)']},
    'siap_pesan': '', 'kurang_bab': [], 'label_kelengkapan': {},
})
cek("5a layar memuat kelas 'done'", 'itm done' in html)
cek("5b layar memuat label 'Done'", '>Done<' in html or 'done-label' in html)
#  'Gap' harus tanpa checkbox
i_gap = html.find('Gap (celah penelitian)')
seg = html[max(0, i_gap - 400):i_gap + 100]
cek("5c 'Gap' TIDAK punya checkbox (blok done)",
    'centangRev' not in seg, seg[-120:].replace('\n', ' '))
#  'Novelty' tetap punya checkbox
i_nov = html.find('Novelty (kebaruan)')
seg2 = html[max(0, i_nov - 400):i_nov + 100]
cek("5d 'Novelty' PUNYA checkbox (masih bisa dibeli)",
    'centangRev' in seg2)

db.query(KonversiNaskah).filter(KonversiNaskah.user_id == u.id,
                                KonversiNaskah.file_id == FID).delete()
db.commit()
db.close()

print()
print("═" * 62)
print(f"  HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL")
if gagal:
    print("  GAGAL: " + ", ".join(gagal))
print("═" * 62)
sys.exit(1 if gagal else 0)
