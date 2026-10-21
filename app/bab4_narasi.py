"""Narasi BAB IV — lahir HANYA dari hasil yang TERKUNCI.

Aturan sumber angka (§13 dokumen induk): semua angka di narasi
diambil dari hasil terkunci (termasuk peta_hipotesis di dalamnya)
dan profil data — AI TIDAK mengarang dan TIDAK membulatkan ulang.
Alur: susun draf deterministik dari angka → poles bahasa dengan AI
lewat pintu tunggal app.ai._panggil_router (system prompt melarang
mengubah angka) → bila AI gagal, draf deterministik tetap dipakai.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from . import bab4
from .models import DataLapanganBab4, HasilBab4, User


def kumpulkan_bahan(db: Session, u: User, file_id: int) -> dict | None:
    """Bahan narasi. None bila belum ada hasil terkunci (gerbang
    Kunci Hasil: narasi tidak lahir dari angka yang masih draf)."""
    terkunci = bab4.hasil_terkunci(db, u.id, file_id, 'olah_data')
    if terkunci is None:
        return None
    hasil = bab4.baca_hasil(terkunci)
    peta_row = (db.query(bab4.PetaBab4)
                .filter_by(user_id=u.id, file_id=file_id)
                .order_by(bab4.PetaBab4.nomor.desc()).first())
    peta = bab4.baca_peta(peta_row) if peta_row else {}
    d = (db.query(DataLapanganBab4)
         .filter_by(user_id=u.id, file_id=file_id, tahap='utama').first())
    masuk = len(json.loads(d.baris or '[]')) if d else 0
    target = d.target_responden if d else None
    pra = (db.query(HasilBab4)
           .filter_by(user_id=u.id, file_id=file_id, jenis='pra_survei')
           .order_by(HasilBab4.nomor.desc()).first())
    kartu = (bab4.kartu_kesehatan(bab4.baca_hasil(pra))
             if pra is not None else None)
    return {'hasil': hasil, 'versi_terkunci': terkunci.nomor,
            'mode': terkunci.mode, 'peta': peta,
            'responden_masuk': masuk, 'target': target,
            'pengembalian': bab4.tingkat_pengembalian(masuk, target),
            'kartu_pra': kartu}


def _fmt(x, bawaan='—'):
    return bawaan if x is None else (f'{x:.4f}' if isinstance(x, float)
                                     else str(x))


def susun_draf(b: dict) -> str:
    """Draf 4.1–4.4 deterministik — angka persis dari hasil."""
    h = b['hasil']
    peta_h = h.get('peta_hipotesis') or []
    variabel = (b['peta'] or {}).get('variabel') or []
    daftar_var = '; '.join(
        f"{v.get('nama')} ({ {'X': 'variabel bebas', 'M': 'variabel perantara', 'Z': 'variabel penguat', 'Y': 'variabel terikat'}.get(v.get('peran'), v.get('peran')) })"
        for v in variabel if isinstance(v, dict))
    L = ['# BAB IV', '# HASIL DAN PEMBAHASAN', '']
    L += ['## 4.1 Gambaran Umum Objek Penelitian', '',
          f'Penelitian ini mengkaji {daftar_var}. '
          f'Data yang kembali dan layak diolah berjumlah '
          f"{b['responden_masuk']} responden"
          + (f" dari target {b['target']} "
             f"({b['pengembalian']}%)." if b['target'] else '.')]
    if b.get('kartu_pra'):
        k = b['kartu_pra']
        L.append('Sebelum penyebaran utama, instrumen diuji coba: '
                 + ('seluruh butir dinyatakan sehat.'
                    if k['semua_sehat'] else
                    f"{len(k['butir_lemah'])} butir diperbaiki "
                    'kata-katanya berdasarkan hasil uji coba.'))
    L += ['', '## 4.2 Hasil Penelitian', '']
    if h.get('r2') is not None:
        L.append(f"Koefisien determinasi (R²) model adalah "
                 f"{_fmt(h.get('r2'))}, artinya variabel bebas "
                 'menjelaskan bagian tersebut dari keragaman variabel '
                 'terikat; sisanya dijelaskan faktor lain di luar model.')
    for e in peta_h:
        if e.get('jenis') == 'interaksi':
            L.append(f"- {e.get('hipotesis')} (moderasi): "
                     f"{e.get('ringkas') or 'lihat hasil moderasi.'}")
        elif e.get('signifikan') is None:
            # TIDAK ADA dasar vonis (p tidak tersedia dan CI tidak
            # ada) — narasi DILARANG mengarang putusan (temuan review
            # ronde 8: efek tidak langsung divonis 'ditolak' padahal
            # mesin tidak memberi p untuk jalur itu).
            L.append(f"- {e.get('hipotesis')}: pengaruh "
                     f"{e.get('dari')} terhadap {e.get('ke')} "
                     f"sebesar {_fmt(e.get('b'))}. Putusan signifikansi "
                     'belum dapat diambil dari hasil ini karena nilai '
                     'p maupun rentang kepercayaan tidak tersedia.')
        elif e.get('p') is None and e.get('lo') is not None:
            L.append(f"- {e.get('hipotesis')}: pengaruh tidak langsung "
                     f"{e.get('dari')} terhadap {e.get('ke')} "
                     f"sebesar {_fmt(e.get('b'))}; rentang kepercayaan "
                     f"95% [{_fmt(e.get('lo'))}, {_fmt(e.get('hi'))}] "
                     f"{'tidak ' if e.get('signifikan') else ''}melewati "
                     'nol — hipotesis '
                     f"{'diterima' if e.get('signifikan') else 'ditolak'} "
                     '(berdasarkan uji bootstrap).')
        else:
            L.append(f"- {e.get('hipotesis')}: pengaruh "
                     f"{e.get('dari')} terhadap {e.get('ke')} "
                     f"sebesar {_fmt(e.get('b'))} dengan nilai "
                     f"signifikansi {_fmt(e.get('p'))}; hipotesis "
                     f"{'diterima' if e.get('signifikan') else 'ditolak'}.")
    L += ['', '## 4.3 Pengujian Hipotesis', '']
    for e in peta_h:
        L.append(f"- {e.get('hipotesis')}: "
                 f"{e.get('ringkas') or 'tidak ditemukan di hasil.'}")
    L += ['', '## 4.4 Pembahasan', '']
    for e in peta_h:
        putusan = ('sejalan dengan hipotesis yang diajukan'
                   if e.get('signifikan') is True else
                   'tidak mendukung hipotesis yang diajukan'
                   if e.get('signifikan') is False else
                   'belum dapat diputuskan dari hasil pengujian ini')
        L.append(f"Hasil pengujian {e.get('hipotesis')} "
                 f"({e.get('dari')} → {e.get('ke')}) {putusan}. "
                 '(Kaitkan temuan ini dengan teori dan penelitian '
                 'terdahulu di Bab II.)')
    return '\n'.join(L) + '\n'


ATURAN_POLES = (
    'Kamu memoles draf BAB IV skripsi berbahasa Indonesia. ATURAN '
    'KERAS: (1) DILARANG mengubah, menambah, atau membulatkan angka '
    'apa pun — semua angka harus persis seperti draf. (2) DILARANG '
    'menambah klaim, teori, nama ahli, atau sitasi baru. (3) Hanya '
    'perbaiki alur kalimat, pilihan kata akademik, dan transisi antar'
    'kalimat. (4) Pertahankan struktur subbab dan daftar butirnya. '
    'Kembalikan teks utuh hasil polesan, tanpa komentar.')


async def poles_ai(draf: str) -> tuple[str, bool]:
    """Poles lewat pintu AI tunggal. (teks, berhasil?) — gagal →
    kembalikan draf asli; narasi tidak boleh gagal total karena AI."""
    try:
        from .ai import _panggil_router
        teks, _info = await _panggil_router(draf, 120.0, system=ATURAN_POLES)
        teks = (teks or '').strip()
        return (teks, True) if teks else (draf, False)
    except Exception:  # noqa: BLE001
        return draf, False

# ── Fase 4: kualitatif & campuran ───────────────────────────────
def susun_pertanyaan_pendalaman(peta_hipotesis: list[dict]) -> list[dict]:
    """Pertanyaan wawancara putaran 2 (campuran) DIBANGUN dari hasil
    kuantitatif terkunci — terutama jalur yang tidak signifikan, sesuai
    desain explanatory sequential (§14 rancangan final). Deterministik:
    kalimatnya templat jujur dari putusan mesin, bukan karangan AI."""
    hasil = []
    for e in (peta_hipotesis or []):
        if not e.get('ketemu'):
            continue
        dari, ke = e.get('dari'), e.get('ke')
        if e.get('jenis') == 'interaksi':
            putusan = 'moderasi'
            q = (f'Hasil hitung menunjukkan pengaruh {dari} terhadap {ke} '
                 'berubah mengikuti variabel penguatnya. Menurut '
                 'Bapak/Ibu, dalam keadaan seperti apa pengaruh itu '
                 'terasa paling kuat di lapangan?')
        elif e.get('signifikan') is True:
            putusan = 'terbukti berpengaruh'
            q = (f'Hasil survei menunjukkan {dari} terbukti berpengaruh '
                 f'terhadap {ke}. Menurut pengalaman Bapak/Ibu, apa '
                 'contoh nyatanya di lapangan — kejadian apa yang '
                 'membuat pengaruh itu terasa?')
        elif e.get('signifikan') is False:
            putusan = 'belum terbukti berpengaruh'
            q = (f'Hasil survei menunjukkan {dari} belum terbukti '
                 f'berpengaruh terhadap {ke}. Menurut Bapak/Ibu, apa '
                 'yang sebenarnya terjadi di lapangan — adakah hal lain '
                 f'yang lebih menentukan {ke}?')
        else:
            putusan = 'belum dapat diputuskan'
            q = (f'Pengaruh {dari} terhadap {ke} belum dapat diputuskan '
                 'dari hasil survei. Menurut Bapak/Ibu, bagaimana '
                 'sebenarnya hubungan keduanya di lapangan?')
        hasil.append({'hipotesis': e.get('hipotesis'), 'dari': dari,
                      'ke': ke, 'putusan': putusan, 'pertanyaan': q})
    return hasil


def kumpulkan_bahan_kualitatif(db: Session, u: User, file_id: int,
                                 jenis: str) -> dict | None:
    """Bahan narasi kualitatif dari hasil matriks TERKUNCI saja."""
    terkunci = bab4.hasil_terkunci(db, u.id, file_id, jenis)
    if terkunci is None:
        return None
    peta_row = (db.query(bab4.PetaBab4)
                .filter_by(user_id=u.id, file_id=file_id)
                .order_by(bab4.PetaBab4.nomor.desc()).first())
    peta = bab4.baca_peta(peta_row) if peta_row else {}
    return {'hasil': bab4.baca_hasil(terkunci),
            'versi_terkunci': terkunci.nomor, 'mode': terkunci.mode,
            'peta': peta, 'jenis': jenis}


def susun_draf_kualitatif(b: dict) -> str:
    """Draf 4.1–4.4 kualitatif dari matriks terkunci (deterministik).

    Angka & kutipan hanya dari hasil mesin; tafsir akhir tetap milik
    peneliti (kalimat draf menyebut dukungan datanya apa adanya).
    """
    peta = b.get('peta') or {}
    _f = peta.get('fokus')
    fokus = ('; '.join(str(x.get('nama') or '') for x in _f
                       if isinstance(x, dict))
             if isinstance(_f, list) else str(_f or '')) \
        or 'fokus penelitian'
    L = ['## 4.1 Gambaran Umum Objek Penelitian',
         '',
         f'Penelitian ini berfokus pada {fokus}. Data kualitatif '
         'dikumpulkan dari informan yang dipilih sesuai peta penelitian '
         'yang telah disahkan.']
    if b.get('jenis') == 'kualitatif_tematik':
        tri = (b.get('hasil') or {}).get('triangulasi') or {}
        temas = tri.get('tema') or []
        L += ['', '## 4.2 Penyajian Data', '']
        if not temas:
            L.append('Belum ada tema yang terbentuk dari koding yang '
                     'disahkan.')
        for t in temas:
            ck = t.get('contoh_kutipan') or {}
            L.append(
                f"Tema {t.get('tema')} didukung {t.get('total_kutipan')} "
                f"kutipan dari {t.get('jumlah_informan')} informan. "
                f"Contoh kutipan: \"{ck.get('teks')}\" "
                f"({ck.get('informan')}).")
            L.append('')
        L += ['## 4.3 Keabsahan Data (Triangulasi)', '']
        for t in temas:
            # Istilah TIDAK boleh tertukar (temuan review Fase 4):
            # informan = ORANGNYA (jumlah_informan), teknik = CARANYA
            # (jumlah_teknik: wawancara/observasi/dokumentasi), jenis
            # informan = internal/eksternal (dasar 'tertriangulasi').
            # Kalimat menyebut ketiga angka dengan namanya masing-
            # masing — versi lama menulis 'satu jenis informan' untuk
            # tema 3 informan 1 teknik, terbaca 'informannya satu'.
            per_jen = t.get('per_jenis') or {}
            n_jen = sum(1 for v in per_jen.values() if v)
            label_jen = ', '.join(k for k, v in per_jen.items() if v)
            tri = ('tertriangulasi sumber (didukung dua jenis informan)'
                   if t.get('tertriangulasi') else
                   'belum tertriangulasi sumber')
            L.append(
                f"Tema {t.get('tema')}: "
                f"{'kuat' if t.get('kuat') else 'perlu diperkuat'} — "
                f"didukung {t.get('jumlah_informan')} informan "
                f"({n_jen} jenis: {label_jen}) melalui "
                f"{t.get('jumlah_teknik')} teknik pengumpulan data; "
                f'{tri}.')
            L.append('')
        L += ['## 4.4 Pembahasan', '',
              'Tema yang kuat dan tertriangulasi menjadi temuan utama '
              'yang dibahas pada bagian ini; tema yang perlu diperkuat '
              'dibahas dengan hati-hati dan ditunjukkan keterbatasannya. '
              'Tafsir akhir atas setiap tema ditulis peneliti dengan '
              'menghubungkannya ke teori pada Bab II.']
    else:  # kualitatif_swot
        sw = (b.get('hasil') or {}).get('swot') or {}
        kel = sw.get('kelompok') or {}
        nama = {'S': 'Kekuatan (Strength)', 'W': 'Kelemahan (Weakness)',
                'O': 'Peluang (Opportunity)', 'T': 'Ancaman (Threat)'}
        L += ['', '## 4.2 Penyajian Data', '']
        for k in 'SWOT':
            daftar = kel.get(k) or []
            L.append(f"{nama[k]}: " + ('; '.join(
                str(x.get('teks')) for x in daftar) or '—') + '.')
            L.append('')
        ifas, efas, kuad = sw.get('ifas') or {}, sw.get('efas') or {}, \
            sw.get('kuadran') or {}
        L += ['## 4.3 Matriks SWOT, IFAS/EFAS, dan Posisi Kuadran', '',
              f"Total skor IFAS { _fmt(ifas.get('total_skor'))} dan EFAS "
              f"{_fmt(efas.get('total_skor'))}."]
        if kuad:
            L.append(f"Posisi objek penelitian berada pada kuadran "
                     f"{kuad.get('label')} (x={_fmt(kuad.get('x'))}, "
                     f"y={_fmt(kuad.get('y'))} dari titik tengah 2,50).")
        for g, nm in ((ifas, 'IFAS'), (efas, 'EFAS')):
            if g and not g.get('bobot_pas_satu'):
                L.append(f"Catatan: total bobot {nm} adalah "
                         f"{_fmt(g.get('total_bobot'))} (idealnya 1,00) — "
                         'sesuaikan bobot sebelum naskah difinalkan.')
        L += ['', '## 4.4 Pembahasan', '',
              'Strategi pada matriks SO, WO, ST, dan WT dibahas pada '
              'bagian ini berdasarkan posisi kuadran di atas; strategi '
              'yang dipilih dihubungkan peneliti dengan kondisi nyata '
              'objek penelitian.']
    return '\n'.join(L)


def susun_draf_campuran(bk: dict, bq: dict) -> str:
    """BAB IV campuran: 4.2 kuantitatif, 4.3 kualitatif, 4.4 terpadu.

    Rangka dari draf kuantitatif (4.1 + hasil) lalu bagian kualitatif
    disisipkan sebelum pembahasan terpadu yang menghubungkan keduanya.
    """
    draf_k = susun_draf(bk)
    tri = (bq.get('hasil') or {}).get('triangulasi') or {}
    temas = tri.get('tema') or []
    L = [draf_k, '', '## 4.3 Hasil Kualitatif (Putaran 2)', '']
    for t in temas:
        ck = t.get('contoh_kutipan') or {}
        L.append(
            f"Tema {t.get('tema')} ({t.get('total_kutipan')} kutipan, "
            f"{t.get('jumlah_informan')} informan): \"{ck.get('teks')}\" "
            f"({ck.get('informan')}).")
        L.append('')
    L += ['## 4.4 Pembahasan Terpadu', '',
          'Pada penelitian campuran ini, temuan kualitatif dipakai '
          'menjelaskan hasil kuantitatif: tema yang muncul dari informan '
          'dihubungkan satu per satu dengan putusan hipotesis pada '
          'bagian 4.2 — terutama jalur yang belum terbukti berpengaruh, '
          'yang memang digali khusus lewat pertanyaan pendalaman. '
          'Peneliti menuliskan hubungan itu dengan kata-katanya sendiri '
          'berdasarkan kutipan pada bagian 4.3.']
    return '\n'.join(L)

