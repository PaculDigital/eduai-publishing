FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz-subset0 \
        libffi-dev \
        shared-mime-info \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY prompts ./prompts

# ── SURVEYOR JEV (14 Okt 2026) ────────────────────────────────────────
# `peta3_jev.py` = SKRIP yang di-COPY apa adanya sebagai /app/peta3_jev.py.
# Dimuat oleh `app/peta3_jev.py` (pembungkus, importlib) lewat jalur '/app/...'.
# ⚠️ BUKAN salinan: berkas di root proyek = satu sumber kebenaran.
# Putusan Bos: peta3_jev menggantikan peta_halus; peta_halus jadi fallback.
COPY peta3_jev.py ./peta3_jev.py

# MESIN BUKU — dipakai /buku/susun (18 Okt 2026).
# ⚠️ SALAH SATU TIDAK BOLEH KETINGGALAN: `penyusunan_buku.py` mengimpor
# `penyusun_buku` → `buku_umum_pipeline` → `tone_menulis` / `jenis_buku` /
# `brief_visual` / `label_infografis` / `larangan_budaya`.
# Kalau cuma sebagian dicopy, rute tetap jalan TAPI gagal saat menyusun.
COPY outline_buku.py ./outline_buku.py
COPY penyusun_buku.py ./penyusun_buku.py
COPY buku_umum_pipeline.py ./buku_umum_pipeline.py
#  Jev di DEPAN penggambar diagram (20 Okt 2026). WAJIB di COPY: tanpa baris
#  ini `import tahapan_diagram` gagal di dalam image ⇒ Jev DIAM-DIAM dilewati
#  dan semua diagram balik ke template, padahal di host tampak "sudah jalan".
COPY tahapan_diagram.py ./tahapan_diagram.py
COPY mutu_isi_buku.py ./mutu_isi_buku.py
COPY jenis_buku.py ./jenis_buku.py
COPY tone_menulis.py ./tone_menulis.py
COPY brief_visual.py ./brief_visual.py
COPY label_infografis.py ./label_infografis.py
COPY larangan_budaya.py ./larangan_budaya.py
COPY verifikasi_sitasi.py ./verifikasi_sitasi.py

#  🚨 DUA BERKAS YANG HAMPIR HILANG DARI PRODUKSI (20 Okt 2026, TERUKUR).
#  `jev_buku_umum.py` = Jev pembaca BENTUK naskah buku. `diagram_buku.py` =
#  penggambar 8 bentuk diagram. Keduanya TIDAK PERNAH ada di Dockerfile,
#  sehingga `import jev_buku_umum` di dalam image GAGAL — dan pemanggilnya
#  (`buku_umum_assembly`) menangkap galat itu LALU JATUH ke jalur regex lama.
#
#  AKIBAT TERUKUR sebelum baris ini ditambahkan:
#    · Container: `ModuleNotFoundError: No module named 'jev_buku_umum'`
#    · Host: Jev jalan sempurna, gerbang 142 LULUS — karena di host
#      berkasnya ADA. Jadi SELURUH uji hijau TIDAK membuktikan produksi.
#
#  ⚠️ PELAJARAN: gerbang yang mengimpor modul dari FOLDER KERJA tidak
#  membuktikan modul itu ikut ke image. Yang membuktikan = `docker exec
#  <c> python3 -c "import <modul>"`.
COPY jev_buku_umum.py ./jev_buku_umum.py
COPY diagram_buku.py ./diagram_buku.py

#  🚨 `tata_paragraf.py` — MODUL INTI YANG JUGA TIDAK PERNAH DI-COPY.
#  Dibuktikan gerbang `gerbang_modul_di_image.py`:
#      import buku_umum_assembly → ModuleNotFoundError: tata_paragraf
#      import buku_umum_pipeline → ModuleNotFoundError: tata_paragraf
#      import jev_buku_umum      → ModuleNotFoundError: tata_paragraf
#  Artinya PERAKIT BUKU gagal total di produksi. Tiga mesin buku
#  mengimpornya: `buku_umum_assembly`, `buku_umum_pipeline`, `jev_buku_umum`.
COPY tata_paragraf.py ./tata_paragraf.py

# ASSEMBLY BUKU — 1 buku jadi SATU .docx (19 Okt 2026, opsi B).
# ⚠️ WAJIB: tanpa berkas ini, `penyusunan_buku.py` gagal merakit dan user
# hanya dapat berkas bab terpisah (tidak bisa dibuka di OnlyOffice).
# Rantai impor: penyusunan_buku → buku_umum_assembly → indeks_referensi (opsional)
COPY buku_umum_assembly.py ./buku_umum_assembly.py
COPY indeks_referensi.py ./indeks_referensi.py

# ── SCRIPT UJI MIRIP (16 Okt 2026) ────────────────────────────────────
# `similarity_precheck.py` = script uji mirip milik Bos (sudah diperbaiki
# bug stabilonya: 11 sumber = 11 stabilo, kotak nomor di atas, sebaran
# alami). Dipakai `app/uji_mirip.py` lewat sys.path.
# ⚠️ Disalin apa adanya = satu sumber kebenaran dengan /opt/data/scripts.
# AKAR 16 Okt: tanpa ini, fitur Uji Plagiarisme balas 500
# "No module named 'similarity_precheck'" — mesinnya di luar image.
COPY similarity_precheck.py ./similarity_precheck.py

# ── LAPORAN UJI (14 Okt 2026) ─────────────────────────────────────────
# Gerbang `app/_gerbang_jev_jalantol.py` (F1/F2) membaca 2 laporan ini
# sebagai BUKTI 12/12. Selama ini berkasnya TIDAK ikut image ⇒ gerbang
# selalu melaporkan 2 GAGAL di produksi (cacat lama, bukan kode).
# Disalin apa adanya = satu sumber kebenaran dengan repo.
COPY HASIL_UJI_12_KASUS_BATAS_09OKT2026.md ./HASIL_UJI_12_KASUS_BATAS_09OKT2026.md
COPY HASIL_VALIDASI_SILANG_K5_09OKT2026.md ./HASIL_VALIDASI_SILANG_K5_09OKT2026.md

# ── Aset statis ───────────────────────────────────────────────────────
# SATU sumber kebenaran = app/static/ (sudah ikut `COPY app ./app` di atas).
#
# CATATAN 12Sep26: folder ./assets/ (duplikat md5-identik) SUDAH DIHAPUS.
# Jangan `COPY assets/...` lagi — folder itu tidak ada, build akan GAGAL
# dengan "file not found in build context".
#
# File yang WAJIB ada di app/static/ (dirujuk kode):
#   logo-96.png, logo-320.png, logo-terang-320.png, hero-bg.svg, eduai.css
# Cek: ls app/static/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
