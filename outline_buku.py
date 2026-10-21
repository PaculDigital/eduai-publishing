"""OUTLINE BUKU dari pilihan user — pengganti MASTER_OUTLINE yang di-hardcode.

KENAPA INI ADA (terukur 18 Okt 2026):
  `MASTER_OUTLINE_SEMENTARA` adalah buku "Ekonomi Digital". Dipakai untuk topik
  "Siklus Hujan" ⇒ 11x kata "ekonomi" + 17x kata "digital" masuk ke prompt
  ⇒ LLM menulis ekonomi padahal topiknya hujan.

  Jadi outline TIDAK BOLEH global. Harus per buku, dibangun dari pilihan user.

API:
    susun_outline(judul, bidang, jenis, jumlah_bab=3, sub_per_bab=3,
                  panggil_llm=None) -> dict
    ke_teks(outline) -> str        # bentuk teks untuk disisipkan ke prompt
    periksa(outline) -> list      # daftar masalah (kosong = sehat)
"""
import json
import re

SUMBER = "outline_buku.py"

#  Jumlah bab default per jenis. Buku anak lebih pendek — anak tidak butuh
#  8 bab; buku profesional butuh lebih banyak supaya layak terbit.
BAB_PER_JENIS = {
    "umum": 6,
    "anak": 3,
    "pendidikan": 5,
}


def _bersih(teks):
    return re.sub(r"\s+", " ", (teks or "")).strip()


def susun_outline(judul, bidang="", jenis="umum", jumlah_bab=None,
                  sub_per_bab=None, panggil_llm=None, bahasa="Indonesia"):
    """Bangun outline buku dari judul + bidang + jenis.

    Return dict yang bentuknya SAMA dengan OUTLINE di pipeline:
        {1: {'title': ..., 'subs': [(nomor, judul, key_points), ...]}, ...}
    plus kunci tambahan '_judul', '_bidang', '_jenis', '_sumber'.

    `panggil_llm` WAJIB fungsi(prompt, max_tokens=...). Kalau tidak diberi,
    dipakai `buku_umum_pipeline.call_llm` (diimpor di dalam fungsi supaya
    tidak ada putaran impor).
    """
    judul = _bersih(judul)
    if not judul:
        raise ValueError("judul buku kosong — outline tidak bisa disusun")

    jenis = (jenis or "umum").strip().lower()
    if jenis not in BAB_PER_JENIS:
        raise ValueError(f"jenis tidak dikenal: {jenis}")

    #  Buku anak: bab sedikit & sub sedikit. Dibatasi supaya tidak jadi
    #  ensiklopedia yang tidak sesuai pembacanya.
    if jumlah_bab is None:
        jumlah_bab = BAB_PER_JENIS[jenis]
    if sub_per_bab is None:
        sub_per_bab = 2 if jenis == "anak" else 3
    jumlah_bab = max(1, min(int(jumlah_bab), 12))
    sub_per_bab = max(1, min(int(sub_per_bab), 6))

    if panggil_llm is None:
        import buku_umum_pipeline as P
        panggil_llm = P.call_llm

    prompt = _prompt_outline(judul, bidang, jenis, jumlah_bab, sub_per_bab, bahasa)
    jawab = panggil_llm(prompt, max_tokens=3000, timeout=120)

    outline = _urai(jawab, jumlah_bab, sub_per_bab, judul, bidang, jenis)
    masalah = periksa(outline)
    if masalah:
        #  Satu percobaan perbaikan. Kalau masih rusak, JANGAN diam-diam
        #  pakai outline separuh — nanti bukunya bolong dan kelihatan "jadi".
        jawab2 = panggil_llm(prompt + "\n\nPERBAIKI: jawaban sebelumnya tidak "
                             "sesuai bentuk. Ikuti bentuk persis.",
                             max_tokens=3000, timeout=120)
        outline2 = _urai(jawab2, jumlah_bab, sub_per_bab, judul, bidang, jenis)
        if not periksa(outline2):
            return outline2
        raise ValueError(f"outline gagal disusun ({len(masalah)} masalah): "
                         f"{masalah[:3]}")
    return outline


def _prompt_outline(judul, bidang, jenis, jumlah_bab, sub_per_bab, bahasa):
    sapaan = {"anak": "anak usia 7-11 tahun",
              "pendidikan": "pelajar/mahasiswa pemula"}.get(jenis, "pembaca umum dewasa")
    return f"""Susun OUTLINE buku berbahasa {bahasa}.

Judul: {judul}
Bidang: {bidang or '(bebas)'}
Pembaca: {sapaan}

ATURAN:
- TEPAT {jumlah_bab} bab, tiap bab TEPAT {sub_per_bab} sub-bab.
- Judul bab & sub-bab harus SPESIFIK untuk judul di atas — bukan judul generik
  yang bisa dipakai buku apa pun.
- Key points: 3-5 frasa pendek, dipisah koma. Harus berupa ISI, bukan janji.
- TIDAK BOLEH menyebut buku lain, TIDAK BOLEH memakai kata "ekonomi digital",
  "transformasi bisnis", atau topik yang tidak diminta.

BENTUK JAWABAN (JSON saja, tanpa penjelasan, tanpa pagar kode):
{{"bab": [
  {{"judul": "...", "sub": [
     {{"judul": "...", "key_points": ["...", "..."]}}
  ]}}
]}}"""


def _urai(teks, jumlah_bab, sub_per_bab, judul, bidang, jenis):
    """Ubah jawaban LLM jadi dict OUTLINE. Toleran terhadap teks pembungkus."""
    if not teks:
        raise ValueError("LLM tidak menjawab (kosong)")
    m = re.search(r"\{.*\}", teks, re.S)
    if not m:
        raise ValueError("jawaban LLM tidak memuat JSON")
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON outline rusak: {e}")

    daftar = data.get("bab") or data.get("chapters") or []
    if not isinstance(daftar, list) or not daftar:
        raise ValueError("JSON outline tidak punya daftar 'bab'")

    out = {"_judul": judul, "_bidang": bidang, "_jenis": jenis, "_sumber": SUMBER}
    n = 0
    for b in daftar:
        if not isinstance(b, dict):
            continue
        bt = _bersih(b.get("judul") or b.get("title"))
        if not bt:
            continue
        n += 1
        subs = []
        for i, s in enumerate(b.get("sub") or b.get("subs") or [], start=1):
            if not isinstance(s, dict):
                continue
            st = _bersih(s.get("judul") or s.get("title"))
            if not st:
                continue
            kp = s.get("key_points") or s.get("keypoints") or []
            if isinstance(kp, list):
                kp = ", ".join(_bersih(x) for x in kp if _bersih(x))
            subs.append((f"{n}.{i}", st, _bersih(kp)))
        out[n] = {"title": bt, "subs": subs}
    return out


def periksa(outline):
    """Daftar masalah outline. Kosong = sehat."""
    masalah = []
    if not isinstance(outline, dict):
        return ["outline bukan dict"]
    nomor = sorted(k for k in outline if isinstance(k, int))
    if not nomor:
        return ["outline tidak punya bab"]
    for k in nomor:
        bab = outline[k]
        if not isinstance(bab, dict) or not _bersih(bab.get("title")):
            masalah.append(f"bab {k}: judul kosong")
            continue
        subs = bab.get("subs") or []
        if not subs:
            masalah.append(f"bab {k}: tidak punya sub-bab")
        for s in subs:
            if len(s) < 3:
                masalah.append(f"bab {k}: bentuk sub-bab salah ({s!r})")
                continue
            if not _bersih(s[1]):
                masalah.append(f"bab {k}: judul sub kosong")
            if not _bersih(s[2]):
                masalah.append(f"bab {k}/{s[0]}: key_points kosong "
                               "(penulis jadi mengarang isi)")
    return masalah


def ke_teks(outline):
    """Bentuk teks untuk disisipkan ke prompt (menggantikan MASTER_OUTLINE)."""
    baris = ["[MASTER OUTLINE — JANGKAR]",
             f"Buku: {outline.get('_judul', '(tanpa judul)')}"]
    if outline.get("_bidang"):
        baris.append(f"Bidang: {outline['_bidang']}")
    baris.append("Tone: DITENTUKAN OLEH JENIS BUKU (lihat bagian TONE di prompt)")
    baris.append("")
    for k in sorted(x for x in outline if isinstance(x, int)):
        bab = outline[k]
        baris.append(f"Bab {k}: {bab['title']}")
        for sub in bab.get("subs") or []:
            baris.append(f"  {sub[0]} {sub[1]}")
            if sub[2]:
                baris.append(f"    → key points: {sub[2]}")
        baris.append("")
    return "\n".join(baris).rstrip()
