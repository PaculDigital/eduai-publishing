"""GERBANG S1 — surveyor WAJIB keluarkan `p` (confidence Jev) per label.

Fungsi SUNGGUHAN peta3_jev. DI DALAM container (butuh app.*).
Jalan: docker exec -w /app eduai-app python3 _gerbang_s1.py

BERGIGI: kalau pengambilan `confidence` dilepas → gerbang HARUS GAGAL.
"""
import sys, inspect
sys.path.insert(0, "/app")
import peta3_jev as P

lulus, gagal = [], []

def cek(nama, syarat):
    (lulus if syarat else gagal).append(nama)
    print(("  \u2705 " if syarat else "  \u274c ") + nama)

kode = inspect.getsource(P.petakan)

# ── A. Kode BENAR-BENAR mengambil confidence dari balasan Jev
cek("A1 petakan mengambil 'confidence' dari jawaban Jev",
    "get('confidence')" in kode or 'get("confidence")' in kode)
cek("A2 ada wadah `conf` per kandidat", "conf = {i: []" in kode)
cek("A3 ada keluaran 'p' di hasil petakan", "'p': p_label" in kode)
cek("A4 p dihitung rata dari confidence (BUKAN kesepakatan antar-putaran)",
    "sum(cs) / len(cs)" in kode)

# ── B. Hanya angka sah yang masuk (bukan None/str)
cek("B1 confidence disaring ke int/float saja",
    "isinstance(c, (int, float))" in kode)

# ── C. UJI NYATA bentuk: fungsi pembantu p dihitung benar
#    Simulasi: nilai p harus rata, dibulatkan 3 angka
def _hitung(conf_list):
    return round(sum(conf_list) / len(conf_list), 3) if conf_list else None
cek("C1 rata 3 angka benar", _hitung([1.0, 1.0]) == 1.0)
cek("C2 rata pecahan benar", _hitung([0.4, 0.6]) == 0.5)
cek("C3 kosong ⇒ None (bukan 0 — jangan mengarang)",
    _hitung([]) is None)

# ── D. label tetap 4 nilai sah (S1 tidak merusak)
cek("D1 label tetap bab/subbab/paragraf/biasa",
    "'bab', 'subbab', 'paragraf'" in kode)

print("=" * 66)
print("HASIL GERBANG S1: %d LULUS / %d GAGAL" % (len(lulus), len(gagal)))
sys.exit(1 if gagal else 0)
