"""Uji FASE 5 — app/konsistensi.py. WAJIB uji nyata, bukan klaim."""
import sys, json
sys.path.insert(0, '/opt/data/services/eduai-publishing')
from app import konsistensi as K

lulus = gagal = 0
def cek(nama, kondisi, info=""):
    global lulus, gagal
    if kondisi:
        lulus += 1; print(f"  ✅ {nama}")
    else:
        gagal += 1; print(f"  ❌ {nama} {info}")

print("═══ 1. ALAT DASAR (normalize/similarity/levenshtein) ═══")
cek("normalize buang tanda baca", K.normalize("Pengaruh, Kualitas! Produk.") == "pengaruh kualitas produk")
cek("normalize None → ''", K.normalize(None) == "")
cek("normalize angka → str", K.normalize(123) == "123")
cek("similarity identik = 1.0", K.similarity("kualitas produk", "kualitas produk") == 1.0)
cek("similarity beda total = 0.0", K.similarity("abcdef", "xyz123") == 0.0)
cek("similarity None = 0.0", K.similarity(None, None) == 0.0)
cek("similarity sebagian (jaccard)", abs(K.similarity("kualitas produk mahasiswa", "kualitas produk") - 2/3) < 0.01)
cek("levenshtein sama = 0", K.levenshtein("kucing", "kucing") == 0)
cek("levenshtein kucing→kucang = 1", K.levenshtein("kucing", "kucang") == 1)
cek("levenshtein kosong", K.levenshtein("", "abc") == 3 and K.levenshtein("abc", "") == 3)
cek("levenshtein None aman", K.levenshtein(None, None) == 0)
cek("levenshtein jauh benar", K.levenshtein("kucing", "mobil") >= 4)
# uji panjang (rolling array, bukan tabel penuh)
panjang_a = "kualitas produk " * 5000
panjang_b = "kualitas produk " * 5000 + "x"
import time
t0 = time.time(); d = K.levenshtein(panjang_a, panjang_b); t1 = time.time()
cek(f"levenshtein 80rb kar tidak lambat ({t1-t0:.2f}s)", d == 1 and (t1-t0) < 30, f"d={d} t={t1-t0:.2f}")
cek("mirip_teks deteksi typo", K.mirip_teks("pengaruh kualitas produk terhadap kepuasan", "pengaruh kualias produk terhadap kepuasan"))
cek("mirip_teks: persis → False", K.mirip_teks("sama", "sama") is False)

print("\n═══ 2. CHECK JUDUL ═══")
judul = "Pengaruh Kualitas Produk terhadap Kepuasan Konsumen"
# 2a: judul persis di paragraf pertama → tidak ada issue
r = K.check_consistency({"judul": judul}, [
    {"section_id": "1.1", "title": "Latar Belakang", "isi_teks": judul + "\nKualitas produk adalah hal penting."}])
cek("2a judul persis → 0 issue", len(r["issues"]) == 0, r["issues"])
cek("2a ok=True", r["ok"] is True)
# 2b: judul mirip tapi tak persis → warning
# ⚠️ DIPERBARUI 16Sep26 (audit Bos): tipe lama "similar_but_not_exact_judul"
# DIGANTI "judul_hampir_persis". Alasannya: judul WAJIB PERSIS menurut kaidah
# akademik; Jaccard (yang mengabaikan urutan kata) tidak boleh jadi penentu.
r = K.check_consistency({"judul": judul}, [
    {"section_id": "1.1", "title": "Latar Belakang", "isi_teks": "Pengaruh Kualitas Barang terhadap Kepuasan Konsumen\nisi lain"}])
cek("2b judul mirip → warning", any(i["type"] == "judul_hampir_persis" for i in r["issues"]), r["issues"])
# 2c: judul bahasa Inggris di lembar persetujuan → TIDAK boleh jadi masalah
r = K.check_consistency({"judul": judul}, [
    {"section_id": "cover", "title": "Cover", "isi_teks": "The Influence of Product Quality on Consumer Satisfaction\napproval page"}])
cek("2c judul asing tidak muncul sbg warning judul", not any(i["jenis"] == "judul" for i in r["issues"]), r["issues"])
# 2d: brief tanpa judul
r = K.check_consistency({}, [{"section_id": "1.1", "isi_teks": "apa saja"}])
cek("2d tanpa judul → summary jujur", "belum terdefinisi" in r["summary"]["judul"])

print("\n═══ 3. CHECK VARIABEL ═══")
brief_var = {"variabel": ["Kualitas Produk", "Kepuasan Konsumen"]}
# 3a: variabel ada semua di 2.1 → 0 issue
r = K.check_consistency(brief_var, [
    {"section_id": "2.1", "title": "Kajian Teori", "isi_teks": "Kualitas Produk dan Kepuasan Konsumen dibahas di sini."}])
cek("3a variabel lengkap → 0 issue", len(r["issues"]) == 0, r["issues"])
# 3b: variabel hilang di 4.1 → warning.
# ⚠️ Diperbarui 16Sep26: bagian yang pendeknya < 400 kar SENGAJA tidak
# diadili (cuma judul/transisi). Jadi teksnya dibuat seperti bahasan asli.
r = K.check_consistency(brief_var, [
    {"section_id": "4.1", "title": "Hasil",
     "isi_teks": "Hasil uji menunjukan nilai signifikan sebesar 0.05. " * 20}])
cek("3b variabel hilang → warning", any(i["type"] == "missing_variable_in_section" for i in r["issues"]), r["issues"])
cek("3b bagian pendek TIDAK diadili", len(K.check_consistency(brief_var, [
    {"section_id": "4.1", "title": "Hasil", "isi_teks": "Hasil uji menunjukan nilai 0.05."}])["issues"]) == 0)
cek("3b tingkat warning, BUKAN error", all(i["level"] == "warning" for i in r["issues"]))
# 3c: kata pertama masih ada → BUKAN masalah
r = K.check_consistency({"variabel": ["Kepuasan Konsumen"]}, [
    {"section_id": "4.4", "title": "Uji Hipotesis", "isi_teks": "Variabel kepuasan diuji dengan regresi."}])
cek("3c kata pertama masih ada → 0 issue", len(r["issues"]) == 0, r["issues"])
# 3d: section di luar daftar wajib → tidak diperiksa
r = K.check_consistency(brief_var, [
    {"section_id": "1.4", "title": "Manfaat", "isi_teks": "Penelitian ini bermanfaat."}])
cek("3d section non-wajib → diabaikan", len(r["issues"]) == 0)
# 3e: variabel berbentuk dict
r = K.check_consistency({"variabel": [{"nama": "Kualitas Produk"}, {"name": "Kepuasan Konsumen"}]}, [])
cek("3e variabel dict terbaca", "2 variabel dicek" in r["summary"]["variabel"], r["summary"])
# 3f: variabel kosong
r = K.check_consistency({"variabel": []}, [{"section_id": "2.1", "isi_teks": "x"}])
cek("3f variabel kosong → jujur", "Tidak ada variabel" in r["summary"]["variabel"])

print("\n═══ 4. CHECK HIPOTESIS ═══")
brief_h = {"hipotesis": ["H1", "H2"]}
st_cocok = [
    {"section_id": "2.4", "title": "Kerangka", "isi_teks": "H1 dan H2 diajukan."},
    {"section_id": "4.4", "title": "Uji", "isi_teks": "H1 diterima, H2 diterima."},
    {"section_id": "5.1", "title": "Kesimpulan", "isi_teks": "H1 dan H2 terbukti."}]
cek("4a hipotesis sinkron → 0 issue", len(K.check_consistency(brief_h, st_cocok)["issues"]) == 0)
st_hilang = [
    {"section_id": "2.4", "title": "Kerangka", "isi_teks": "H1 dan H2 diajukan."},
    {"section_id": "4.4", "title": "Uji", "isi_teks": "H1 saja diterima."}]
r = K.check_consistency(brief_h, st_hilang)
cek("4b H2 hilang di 4.4 → ERROR", any(i["type"] == "hipotesis_mismatch_2.4_4.4" and i["level"] == "error" for i in r["issues"]), r["issues"])
cek("4b ok=False", r["ok"] is False)
st_51 = st_cocok[:1] + [{"section_id": "5.1", "title": "Kesimpulan", "isi_teks": "H1 terbukti, H3 juga."}]
r = K.check_consistency(brief_h, st_51)
cek("4c 5.1 beda → ERROR", any(i["type"] == "hipotesis_mismatch_2.4_5.1" for i in r["issues"]), r["issues"])
cek("4d tanpa hipotesis → jujur", "Tidak ada hipotesis" in K.check_consistency({}, [])["summary"]["hipotesis"])
cek("4e hipotesis string tunggal aman", "1 hipotesis dicek" in K.check_consistency({"hipotesis": "H1"}, [])["summary"]["hipotesis"])
# hipotesis sampai 12 (tesis mediasi ganda — koreksi Bos §4.16)
hip12 = {"hipotesis": [f"H{i}" for i in range(1, 13)]}
st12 = [
    {"section_id": "2.4", "isi_teks": " ".join(f"H{i}" for i in range(1, 13))},
    {"section_id": "4.4", "isi_teks": " ".join(f"H{i}" for i in range(1, 13))},
    {"section_id": "5.1", "isi_teks": " ".join(f"H{i}" for i in range(1, 13))}]
r = K.check_consistency(hip12, st12)
cek("4f 12 hipotesis (tesis mediasi ganda) sinkron", len(r["issues"]) == 0, r["issues"])
cek("4f hitung 12", "12 hipotesis dicek" in r["summary"]["hipotesis"])

print("\n═══ 5. CHECK OV ═══")
cek("5a ada tanda OV → 0 issue", len(K.check_consistency({}, [{"section_id": "3.1", "isi_teks": 'Variabel "Kualitas Produk" X1 diukur.'}])["issues"]) == 0)
r = K.check_consistency({}, [{"section_id": "3.1", "isi_teks": "Definisi operasional dijelaskan secara naratif saja."}])
cek("5b tanpa tanda OV → info", any(i["type"] == "no_ov_detected" for i in r["issues"]), r["issues"])
cek("5b level info (bukan error)", r["ok"] is True)
cek("5c 3.1 kosong → jujur", "belum terdefinisi" in K.check_consistency({}, [{"section_id": "3.1", "isi_teks": ""}])["summary"]["ov"])

print("\n═══ 6. TAHAN DATA ANEH ═══")
for nama, args in [
    ("brief None", (None, None)),
    ("brief string JSON", ('{"judul":"X"}', [])),
    ("brief string rusak", ('{bukan json', [])),
    ("brief list", ([1, 2, 3], [])),
    ("sections None", ({"judul": "A"}, None)),
    ("section isi None", ({"judul": "A"}, [{"section_id": "1.1", "isi_teks": None}])),
    ("section dict kosong", ({}, [{}])),
    ("section berisi angka", ({}, [{"section_id": "1.1", "isi_teks": 12345}])),
    ("section tanpa section_id", ({"judul": "A"}, [{"isi_teks": "halo"}])),
]:
    try:
        r = K.check_consistency(*args)
        cek(f"6 {nama} tidak crash", isinstance(r.get("summary"), dict))
    except Exception as e:
        cek(f"6 {nama} tidak crash", False, f"→ {type(e).__name__}: {e}")

print("\n═══ 7. LAPORAN + KATA TERLARANG ═══")
brief_penuh = {"judul": judul, "variabel": ["Kualitas Produk"], "hipotesis": ["H1"]}
states_buruk = [
    {"section_id": "2.4", "title": "Kerangka", "isi_teks": "H1 diajukan."},
    {"section_id": "4.4", "title": "Uji", "isi_teks": "H1 dan H2 diterima."},
    {"section_id": "5.1", "title": "Kesimpulan", "isi_teks": "H1 terbukti."},
    {"section_id": "3.1", "title": "Metode", "isi_teks": "naratif saja"}]
r = K.check_consistency(brief_penuh, states_buruk)
laporan = K.format_laporan(r)
print(laporan)
cek("7a laporan string", isinstance(laporan, str) and len(laporan) > 30)
terlarang = ["kuota", "token ai", "rupiah", "rp ", "addon", "token revisi"]
low = laporan.lower()
cek("7b laporan bersih kata terlarang", not any(t in low for t in terlarang), [t for t in terlarang if t in low])
cek("7c format_laporan(None) aman", "gagal" in K.format_laporan(None).lower())
cek("7d catatan_untuk_ai kosong bila bersih", K.catatan_untuk_ai(K.check_consistency({}, [])) == "")
cek("7e catatan_untuk_ai ADA bila ada issue", len(K.catatan_untuk_ai(r)) > 50)

print("\n═══ 8. UJI NASKAH NYATA (tesis Bos) ═══")
import glob, os
kandidat = glob.glob('/opt/data/services/eduai-publishing/_arsip/**/*.docx', recursive=True)
print(f"  docx ditemukan: {len(kandidat)}")
if kandidat:
    try:
        sys.path.insert(0, '/opt/data/services/eduai-publishing')
        from app import versi, state
        path = max(kandidat, key=os.path.getsize)
        print(f"  pakai: {os.path.basename(path)} ({os.path.getsize(path)/1e6:.2f} MB)")
        teks = versi.ekstrak_teks(path) if hasattr(versi, 'ekstrak_teks') else None
        if teks is None:
            for nm in ('ambil_teks','baca_docx','ekstrak'):
                if hasattr(versi, nm):
                    teks = getattr(versi, nm)(path); break
        if teks:
            print(f"  teks: {len(teks)} kar")
            peta = state.petakan(teks) if hasattr(state, 'petakan') else None
            if peta is None: peta = state.petakan(teks)
            print(f"  peta bab: {len(peta) if peta else 0} bagian")
            rows = [{"section_id": (p.get('section_id') or p.get('id') or ''), "title": p.get('judul') or p.get('title') or '', "isi_teks": p.get('isi') or p.get('teks') or ''} for p in (peta or [])]
            r = K.check_consistency(brief_penuh, rows)
            print(f"  hasil: {r['summary']['counts']} · ok={r['ok']}")
            cek("8 uji naskah nyata tidak crash", True)
            cek("8 ada section terbaca", len(rows) > 0, f"{len(rows)} row")
        else:
            cek("8 ekstrak teks naskah nyata", False, "fungsi ekstrak tidak ditemukan di versi.py")
    except Exception as e:
        import traceback; traceback.print_exc()
        cek("8 uji naskah nyata", False, str(e))

print(f"\n{'='*60}\nHASIL: {lulus} LULUS / {gagal} GAGAL\n{'='*60}")
sys.exit(1 if gagal else 0)
