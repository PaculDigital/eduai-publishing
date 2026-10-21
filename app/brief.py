"""Research Brief — "kebenaran tunggal" isi penelitian.

=== SALINAN POLA DARI PENELITIAN-BOT (SUMBER READ-ONLY) ===
Asal: /opt/data/services/penelitian-bot/telegram-bot/research-brief.js
      baris 4-13  -> BRIEF_TEMPLATE
      baris 16-23 -> initBrief()
      baris 26-35 -> updateSection()
      baris 38-47 -> addNote()
      baris 88-92 -> approveBrief()   (briefStatus: draft|review|approved)
      baris 99-143 -> formatBriefSummary()

KENAPA DIBUAT: SEMUA bagian naskah (BAB I–V) WAJIB patuh ke satu sumber ini,
supaya tidak terjadi "kata tidak nyambung" antar bab. Kalau AI merevisi Bab IV
tapi lupa variabel di Bab II, celah inilah penangkalnya.

ADAPTASI (jangan copy buta):
  - Node/Prisma  ->  Python/SQLAlchemy.
  - `catatan[]`  ->  JSON list di kolom brief_json (tidak tabel terpisah).
  - `draftDocId` / `finalDocId` (Google Docs) -> TIDAK dipakai EduAi
    (EduAi menyimpan berkas sendiri di tabel files/versi_dokumen).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)


# ── Pola brief — research-brief.js baris 4-13 ───────────────────────────
# Isi `pf` (problem formulation) & `li` (literature) diadopsi dari
# problem-formulation.js baris 23-35 dan research-brief.js formatBriefSummary.
BRIEF_TEMPLATE: dict[str, Any] = {
    # Hasil pengenalan naskah (ROLE 1 Pengenal) — MASTER_PLAN §4.11
    'jenis': None,            # 'skripsi' | 'tesis' | 'disertasi' | 'proposal' | 'jurnal' | 'umum'
    'kategori': None,         # 'akademik_1bab' | 'akademik_proposal' | 'akademik_lengkap' | 'dokumen_umum'
    'paradigma': None,        # 'kuantitatif' | 'kualitatif' | 'slr' | 'non_ilmiah'

    # ALUR ARGUMENTASI — MASTER_PLAN §4.14 (hasil putusan AI, BUKAN tanya user)
    'alur': None,             # 'kuantitatif_deduktif' | 'kualitatif_induktif' | 'kualitatif_deduktif'
    'alur_alasan': '',        # kenapa alur ini dipilih (ditampilkan ke user 1x)

    # Problem Formulation — problem-formulation.js baris 23-35
    'judul': None,
    'fenomena': None,
    'rumusan_masalah': None,
    'pertanyaan_penelitian': [],
    'tujuan': None,
    'manfaat_teoritis': None,
    'manfaat_praktis': None,

    # Variabel & hipotesis (dipakai consistency-checker, §4.15 komponen 6)
    'variabel': [],           # [{'nama': 'X1', 'jenis': 'independen'}, ...]
    'hipotesis': [],          # ['H1', 'H2', ...]

    # Metodologi — research-brief.js formatBriefSummary
    'metodologi': None,       # {'desain': ..., 'sampel': ..., 'alat_ukur': ..., 'analisis': ...}

    # Kitab Istilah — MASTER_PLAN §4.12 (kunci istilah agar tidak gonta-ganti)
    'istilah': [],            # [{'istilah': 'QWL', 'arti': '...'}, ...]

    # Catatan diskusi — research-brief.js baris 130-136
    'catatan': [],            # [{'text': '...', 'timestamp': '...'}, ...]

    # Struktur dokumen — MASTER_PLAN §4.11 (struktur_json)
    'struktur': [],           # [{'nomor': 'BAB I', 'judul': 'PENDAHULUAN', 'karakter': 43000}, ...]

    # Sidik jari isi dokumen (SHA-256) — deteksi naskah berubah
    'sidik_jari': None,
}

# Kunci yang TIDAK boleh ditimpa user/AI (dihitung sistem)
_KUNCI_SISTEM = {'sidik_jari', 'struktur', 'alur', 'kategori'}


def brief_kosong() -> dict[str, Any]:
    """Brief baru berisi template (salinan dalam, bukan referensi)."""
    return json.loads(json.dumps(BRIEF_TEMPLATE))


def muat(brief_json: str | None) -> dict[str, Any]:
    """Baca brief dari kolom TEXT di DB.

    Aman terhadap: NULL, string kosong, JSON rusak, JSON bukan objek.
    (Pelajaran EduAi: JANGAN percaya bentuk data dari DB — selalu jaga.)
    """
    if not brief_json or not brief_json.strip():
        return brief_kosong()
    try:
        data = json.loads(brief_json)
    except (json.JSONDecodeError, TypeError):
        log.warning('[brief] JSON rusak, pakai template kosong')
        return brief_kosong()
    if not isinstance(data, dict):
        return brief_kosong()
    # lengkapi kunci yang hilang (brief lama / versi sebelumnya)
    dasar = brief_kosong()
    dasar.update({k: v for k, v in data.items() if k in BRIEF_TEMPLATE})
    return dasar


def simpan(brief: dict[str, Any]) -> str:
    """Serialisasi brief untuk disimpan ke kolom TEXT."""
    aman = {k: brief.get(k, BRIEF_TEMPLATE[k]) for k in BRIEF_TEMPLATE}
    return json.dumps(aman, ensure_ascii=False)


def perbarui(brief_json: str | None, **nilai: Any) -> str:
    """Perbarui sebagian kunci brief.

    research-brief.js updateSection() baris 26-35.
    Kunci sistem (alur/kategori/struktur/sidik_jari) HANYA boleh diisi
    oleh modul sistem — kalau AI/user mencoba, ditolak dengan log.
    """
    brief = muat(brief_json)
    for kunci, nilai_baru in nilai.items():
        if kunci not in BRIEF_TEMPLATE:
            log.debug('[brief] kunci tak dikenal diabaikan: %s', kunci)
            continue
        if kunci in _KUNCI_SISTEM and brief.get(kunci) not in (None, [], '', {}):
            log.info('[brief] kunci sistem %s sudah terisi — tidak ditimpa', kunci)
            continue
        brief[kunci] = nilai_baru
    return simpan(brief)


def tambah_catatan(brief_json: str | None, teks: str) -> str:
    """Tambah catatan diskusi — research-brief.js addNote() baris 38-47."""
    brief = muat(brief_json)
    catatan = brief.get('catatan') or []
    if not isinstance(catatan, list):
        catatan = []
    catatan.append({
        'text': (teks or '').strip()[:2000],
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })
    brief['catatan'] = catatan[-100:]          # jaga ukuran
    return simpan(brief)


def ringkas(brief: dict[str, Any]) -> str:
    """Ringkasan terbaca — research-brief.js formatBriefSummary() baris 99-143.

    Dipakai untuk LOG & panel admin (bukan untuk ditampilkan mentah ke user).
    """
    if not brief:
        return '(brief kosong)'
    baris: list[str] = []
    if brief.get('judul'):
        baris.append(f"Judul    : {brief['judul']}")
    if brief.get('paradigma'):
        baris.append(f"Paradigma: {brief['paradigma']} ({brief.get('alur') or 'alur belum ditetapkan'})")
    if brief.get('kategori'):
        baris.append(f"Kategori : {brief['kategori']}")
    var = brief.get('variabel') or []
    if var:
        nama = [v.get('nama', '?') if isinstance(v, dict) else str(v) for v in var]
        baris.append(f"Variabel : {', '.join(nama)}")
    hip = brief.get('hipotesis') or []
    if hip:
        baris.append(f"Hipotesis: {', '.join(str(h) for h in hip)}")
    met = brief.get('metodologi')
    if isinstance(met, dict) and met.get('desain'):
        baris.append(f"Desain   : {met['desain']}")
    ist = brief.get('istilah') or []
    if ist:
        baris.append(f"Istilah  : {len(ist)} kunci")
    struktur = brief.get('struktur') or []
    if struktur:
        baris.append(f"Struktur : {len(struktur)} bagian")
    return '\n'.join(baris) if baris else '(brief kosong)'
