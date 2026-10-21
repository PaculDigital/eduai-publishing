"""PERIKSA: mengapa E1 gagal — pagar terlalu ketat atau AI yang aneh?

Membaca proses_ai terakhir + MEMANGGIL ULANG pipa pada data yang sama
untuk melihat angka sebenarnya (panjang kutip vs panjang ganti).
"""
import json
import sqlite3
import sys

sys.path.insert(0, '/app')

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row
r = c.execute("""SELECT id,kode,status,galat,panjang,file_id,jumlah_bagian,
                        model_ai,token_in,token_out,hasil_json,hasil,komentar_json,jenis_dokumen,dibuat
                 FROM proses_ai ORDER BY id DESC LIMIT 6""").fetchall()

print('═' * 96)
print('  PROSES_AI TERAKHIR')
print('═' * 96)
for x in r:
    print(f"id={x['id']} status={x['status']} panjang={x['panjang']} bagian={x['jumlah_bagian']} "
          f"model={x['model_ai']} in={x['token_in']} out={x['token_out']}")
    print(f"   kode={x['kode']} file={x['file_id']} jenis={x['jenis_dokumen']} dibuat={x['dibuat']}")
    if x['galat']:
        print(f"   GALAT: {x['galat'][:180]}")
    # apakah hasil_json memuat daftar DITOLAK (angka panjang)?
    if x['hasil_json']:
        try:
            h = json.loads(x['hasil_json'])
            for k in ('ditolak', 'profil', 'cakupan'):
                if k in h and h[k]:
                    v = h[k]
                    s = json.dumps(v, ensure_ascii=False)[:400]
                    print(f"   {k}: {s}")
        except Exception as e:                                   # noqa: BLE001
            print(f"   hasil_json tak terbaca: {e}")
    if x['komentar_json']:
        try:
            k = json.loads(x['komentar_json'])
            print(f"   KOMENTAR ({len(k) if isinstance(k, list) else '?'} butir): "
                  f"{json.dumps(k, ensure_ascii=False)[:400]}")
        except Exception:                                        # noqa: BLE001
            print(f"   komentar_json: {str(x['komentar_json'])[:200]}")
    print('─' * 96)

print()
print('PAGAR (app/pipa.py:70): PANJANG_MAKS_KALI = 3.0  → ganti ≤ 3× paragraf')
print('                              minimum      = 200 kar')
print()
print('Arti: kalau AI mengembalikan jawaban >3× panjang bagian yang diminta,')
print('      ditolak sebagai "balasan tidak wajar".')
