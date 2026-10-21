"""Mesin PENCARIAN REFERENSI TERVERIFIKASI untuk EduAi.

📌 ASAL (bukan bikin baru — sesuai arahan Bos 26Sep26 "kamu cek dulu di kode,
   dan copy jadikan skill pencarian di EduAi ini"):
   Disalin dari /opt/data/services/jurnalkit/phase1_harvest_v2.py (1.044 baris)
   — HANYA bagian PENCARIAN. Bagian Google Drive (upload_daftar_pustaka,
   get_drive_service, dst) TIDAK dibawa: EduAi menulis hasil langsung ke
   naskah mahasiswa, tidak perlu Drive.

📌 4 SUMBER (semua WAJIB dicoba; 1 gagal → sisanya tetap jalan = failover):
   1. Scopus    — API key (X-ELS-APIKey), jurnal internasional Q1-Q4
   2. OpenAlex  — API key (query param!), 240jt artikel + citation count
   3. Garuda    — HTML scrape Kemdiktisaintek, jurnal Indonesia/SINTA
   4. CrossRef  — AUDIT DOI semua sumber (anti-halusinasi)

📌 PRINSIP ANTI-HALUSINASI (aturan Bos, tidak boleh dilanggar):
   · AI DILARANG mengarang sitasi
   · Setiap referensi WAJIB punya DOI/URL yang bisa ditrace
   · DOI dari Scopus/OpenAlex WAJIB diaudit ke CrossRef sebelum dipakai
   · Hanya referensi terverifikasi yang boleh masuk daftar pustaka

📌 JEBAKAN YANG SUDAH DIKETAHUI (dari skill sumber-referensi-terverifikasi):
   · Scopus: WAJIB pakai requests + params (jangan encode manual) →
     kalau salah, HTTP 200 tapi 0 hasil
   · OpenAlex: api_key di QUERY PARAM, bukan header; filter OR antar nilai
     (type:a|type:b) = 400 Bad Request
   · Garuda: 302 redirect WAJIB di-follow; User-Agent WAJIB diset;
     query PER kata kunci (gabungan → balas "0 document")
   · Keyword stop words: "pengaruh", "terhadap", "pada" → 0 hasil

📌 KONTEKS PEMAKAIAN: dipakai untuk "KERANGKA PER BAB" (arahan Bos
   26Sep26) — mesin mencari sitasi sesuai TEMA + JUDUL penelitian, lalu
   kerangka bab disusun dari artikel TERVERIFIKASI.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

log = logging.getLogger('eduai.pustaka')

# ── Batas & filter (keputusan Bos: tahun 2019-2026, longgarkan bila <10) ──
TAHUN_AWAL = 2019
TAHUN_AKHIR = 2026
MAKS_PER_SUMBER = 15          # Scopus 15 · OpenAlex 15 · Garuda 10
MAKS_GARUDA = 10

SCOPUS_URL = 'https://api.elsevier.com/content/search/scopus'
OPENALEX_URL = 'https://api.openalex.org'
GARUDA_URL = 'https://garuda.kemdiktisaintek.go.id/documents'
CROSSREF_URL = 'https://api.crossref.org/works'

# ── KUNCI MESIN PENCARI (12Okt26) ────────────────────────────────────────
#  ⚠️ ATURAN: kunci WAJIB JELAS, bukan diam-diam (perintah Bos 12Okt26).
#  POLA SAMA dengan kunci lain proyek ini (`EDUAI_ROUTER_KEY`,
#  `PAKASIR_API_KEY`) → dibaca dari ENVIRONMENT (diisi oleh `.env` lewat
#  `--env-file` di jalankan.sh). TIDAK ada berkas rahasia di luar .env.
#
#  KENAPA DIUBAH 12Okt26: sebelumnya kunci dicari dari berkas JSON di
#  `/app/_rahasia/` — folder itu TIDAK PERNAH masuk container (tidak ada
#  mount-nya) ⇒ Scopus SELALU dilewati diam-diam. Sekarang lewat `.env`.
#
#  KENAPA DIUBAH 13Okt26: Bos minta bisa GANTI KUNCI SENDIRI dari
#  dashboard admin (`/pengaturan`) tanpa deploy. Kunci kini dibaca lewat
#  `kunci_layanan.ambil()` — urutan: berkas admin (`data/kunci-layanan.json`)
#  → `.env` → ''. Fungsi dipanggil SAAT PAKAI (bukan saat impor) supaya
#  kunci yang baru ditempel admin langsung terpakai tanpa restart.
def _kunci(nama: str, env: str) -> str:
    try:
        from .kunci_layanan import ambil
        return ambil(nama) or os.getenv(env, '')
    except Exception:                                            # noqa: BLE001
        return os.getenv(env, '')


SCOPUS_KEY = os.getenv('EDUAI_SCOPUS_KEY', '')      # bawaan (cadangan)
OPENALEX_KEY = os.getenv('EDUAI_OPENALEX_KEY', '')   # bawaan (cadangan)
#  Email "polite" untuk OpenAlex (etika API — bukan rahasia).
EMAIL_POLITE = os.getenv('EDUAI_EMAIL_POLITE', 'paculdigital03@gmail.com')

# ── KAMUS KONSEP (ID → sinonim EN & ID) ──────────────────────────────────
#  Dipakai untuk menyusun RUMUS PICO: tiap KONSEP jadi satu grup (OR di
#  dalamnya), lalu antar konsep digabung dengan AND.
KAMUS_KONSEP: dict[str, dict] = {
    'aktivitas fisik': {'en': ['physical activity', 'exercise', 'training'],
                        'id': ['aktivitas fisik', 'latihan fisik', 'olahraga']},
    'siklus menstruasi': {'en': ['menstrual cycle', 'menstruation',
                                 'menstrual'],
                          'id': ['siklus menstruasi', 'menstruasi']},
    'amenore': {'en': ['amenorrhea', 'amenorrhoea'],
                'id': ['amenore', 'amenorea']},
    'atlet': {'en': ['athlete', 'athletes', 'sportswoman', 'sports women'],
              'id': ['atlet', 'atlet wanita', 'olahragawan']},
    'remaja': {'en': ['adolescent', 'adolescents', 'teenager'],
               'id': ['remaja', 'remaja putri']},
    'keputusan pembelian': {'en': ['purchase decision', 'buying decision'],
                            'id': ['keputusan pembelian']},
    'kualitas produk': {'en': ['product quality'], 'id': ['kualitas produk']},
    'harga': {'en': ['price', 'pricing'], 'id': ['harga']},
    'promosi': {'en': ['promotion', 'advertising'],
                'id': ['promosi', 'iklan']},
    'kepuasan kerja': {'en': ['job satisfaction'], 'id': ['kepuasan kerja']},
    'kinerja karyawan': {'en': ['employee performance', 'job performance'],
                         'id': ['kinerja karyawan', 'kinerja pegawai']},
    'kepemimpinan': {'en': ['leadership'], 'id': ['kepemimpinan']},
    'motivasi': {'en': ['motivation'], 'id': ['motivasi']},
    'minat belajar': {'en': ['learning interest'], 'id': ['minat belajar']},
    'hasil belajar': {'en': ['learning outcome', 'learning achievement',
                             'academic achievement'],
                      'id': ['hasil belajar', 'prestasi belajar']},
    'literasi digital': {'en': ['digital literacy'], 'id': ['literasi digital']},
    'umkm': {'en': ['SME', 'small medium enterprise', 'MSME'],
             'id': ['umkm', 'usaha mikro kecil menengah']},
    'ekonomi digital': {'en': ['digital economy'], 'id': ['ekonomi digital']},
    'tata kelola': {'en': ['governance'], 'id': ['tata kelola']},
    'etika bisnis': {'en': ['business ethics'], 'id': ['etika bisnis']},
    'pendidikan tinggi': {'en': ['higher education'], 'id': ['pendidikan tinggi']},
    'kesehatan mental': {'en': ['mental health', 'psychological well-being'],
                         'id': ['kesehatan mental']},
    'kecemasan': {'en': ['anxiety', 'anxiety disorder'], 'id': ['kecemasan']},
    'cricket': {'en': ['cricket'], 'id': ['kriket', 'kricket']},
    'cedera': {'en': ['injury', 'injuries'], 'id': ['cedera', 'cidera']},
}

_KATA_HENTI = {
    'pengaruh', 'terhadap', 'pada', 'di', 'dan', 'atau', 'dengan', 'dari',
    'untuk', 'dalam', 'yang', 'ini', 'ke', 'oleh', 'sebagai', 'antara',
    'serta', 'tentang', 'studi', 'kasus', 'analisis', 'the', 'of', 'on',
}


def cari_scopus(kw_en: list[str], maks: int = MAKS_PER_SUMBER,
                query_siap: str = '') -> list[dict]:
    """Cari di Scopus. Gagal → [] (failover, JANGAN hentikan pencarian).

    🔴 RUMUS BENAR (26Sep26): AND antar KONSEP, OR di dalam konsep.
       `query_siap` = hasil `rumus_scopus(konsep)` — kalau kosong, jatuh ke
       cara lama (daftar kata kunci dalam satu frasa) supaya tetap jalan.
    """
    _sk = _kunci('scopus', 'EDUAI_SCOPUS_KEY')
    if not _sk:
        log.warning('[pustaka] Scopus: kunci tidak ada → dilewati')
        return []
    try:
        #  ⚠️ WAJIB httpx + params (jangan encode manual — bisa 200 tapi 0).
        if query_siap:
            query = query_siap
        else:
            bagian = [f'TITLE-ABS-KEY("{k}")' for k in (kw_en or []) if k.strip()]
            if not bagian:
                return []
            query = bagian[0] if len(bagian) == 1 else (
                f'{bagian[0]} AND ({bagian[1]}' + ''.join(
                    f' OR {b}' for b in bagian[2:]) + ')')
        params = {'query': query, 'count': maks,
                  'sort': 'citedby', 'date': f'{TAHUN_AWAL}-{TAHUN_AKHIR}'}
        r = httpx.get(SCOPUS_URL, params=params, timeout=30,
                         headers={'X-ELS-APIKey': _kunci('scopus', 'EDUAI_SCOPUS_KEY'),
                                  'Accept': 'application/json'})
        if r.status_code != 200:
            log.warning('[pustaka] Scopus HTTP %s → dilewati', r.status_code)
            return []
        keluar = []
        for it in (r.json().get('search-results', {}).get('entry') or []):
            doi = it.get('prism:doi') or ''
            if doi and not doi.startswith('http'):
                doi = 'https://doi.org/' + doi
            th = 0
            m = re.search(r'(\d{4})', str(it.get('prism:coverDate') or ''))
            if m:
                th = int(m.group(1))
            keluar.append({
                'title': (it.get('dc:title') or '').strip(),
                'doi': doi, 'year': th,
                'authors': it.get('dc:creator') or '',
                'cited_by_count': int(it.get('citedby-count') or 0),
                'source': 'Scopus', 'abstract': it.get('dc:description') or '',
                'journal': it.get('prism:publicationName') or '',
                #  ⭐ MUTU JURNAL (12Okt26): ISSN dipakai ambil SJR/CiteScore.
                #     Hasil Scopus MEMANG mengirim prism:issn — dipakai apa adanya.
                'issn': (it.get('prism:issn') or '').split(',')[0].strip(),
                'garuda_id': None,
            })
        log.info('[pustaka] Scopus: %s hasil', len(keluar))
        return keluar
    except Exception as e:                                    # noqa: BLE001
        log.warning('[pustaka] Scopus error: %s', e)
        return []


# ══════════════════════════════════════════════════════════════════════════
#  SUMBER 2 — OPENALEX (+ abstract + jumlah sitasi)
# ══════════════════════════════════════════════════════════════════════════
def _abstrak_openalex(inv: dict | None) -> str:
    if not isinstance(inv, dict):
        return ''
    pasangan = []
    for kata, posisi in inv.items():
        if isinstance(posisi, list):
            for p in posisi:
                pasangan.append((p, kata))
    pasangan.sort()
    return ' '.join(k for _, k in pasangan)


def cari_openalex(kw_en: list[str], kw_id: list[str] | None = None,
                  maks: int = MAKS_PER_SUMBER, frasa: str = '') -> list[dict]:
    """OpenAlex: 2 query (EN global + ID language:id) — dari jurnalkit."""
    try:
        hdr = {'User-Agent': f'OpenAlexBot/1.0 (mailto:{EMAIL_POLITE})'}
        kumpul, lihat = [], set()

        def _tarik(par: dict) -> None:
            r = httpx.get(f'{OPENALEX_URL}/works', params=par,
                             headers=hdr, timeout=30)
            if r.status_code != 200:
                log.warning('[pustaka] OpenAlex HTTP %s', r.status_code)
                return
            for it in (r.json().get('results') or []):
                wid = it.get('id')
                if wid and wid not in lihat:
                    lihat.add(wid)
                    kumpul.append(it)

        dasar = (f'from_publication_date:{TAHUN_AWAL}-01-01,'
                 f'to_publication_date:{TAHUN_AKHIR}-12-31')
        #  ⚠️ api_key = QUERY PARAM (bukan header). Filter OR antar nilai = 400.
        #  🔴 pakai frasa KONSEP INTI (dari PICO) — bukan gabungan kata bebas
        _frasa_en = frasa or ' '.join(
            [k for k in kw_en if len(k) > 2][:1]) or \
            ' '.join([k for k in (kw_id or []) if len(k) > 3][:1])
        p1 = {'filter': dasar, 'search': _frasa_en,
              'sort': 'cited_by_count:desc', 'per_page': min(maks, 7)}
        if _kunci('openalex', 'EDUAI_OPENALEX_KEY'):
            p1['api_key'] = _kunci('openalex', 'EDUAI_OPENALEX_KEY')
        _tarik(p1)
        if kw_id:
            p2 = {'filter': dasar + ',language:id', 'search': ' '.join(
                [k for k in kw_id if len(k) > 3][:4]),
                'sort': 'cited_by_count:desc', 'per_page': min(maks, 10)}
            if _kunci('openalex', 'EDUAI_OPENALEX_KEY'):
                p2['api_key'] = _kunci('openalex', 'EDUAI_OPENALEX_KEY')
            _tarik(p2)

        kumpul.sort(key=lambda x: x.get('cited_by_count') or 0, reverse=True)
        keluar = []
        for it in kumpul[:maks]:
            try:
                doi = it.get('doi')
                if isinstance(doi, str) and doi.startswith('10.'):
                    doi = 'https://doi.org/' + doi
                elif not isinstance(doi, str):
                    doi = ''
                penulis = []
                for a in (it.get('authorships') or []):
                    if isinstance(a, dict):
                        n = a.get('display_name') or \
                            (a.get('author') or {}).get('display_name', '')
                        if n:
                            penulis.append(n)
                lok = it.get('primary_location')
                jurnal = ''
                if isinstance(lok, dict):
                    src = lok.get('source')
                    jurnal = src.get('display_name', '') \
                        if isinstance(src, dict) else ''
                #  ── TAUTAN PDF (06Okt26) ─────────────────────────────────
                #  ⚠️ AKAR celah: rute /jurnal/unduh ADA, tapi artikel masuk
                #  TANPA pdf_url → unduh_pdf() selalu bilang "tidak
                #  menyertakan tautan PDF" ⇒ fitur tampak selesai, tak guna.
                #  OpenAlex SUDAH menyediakan `open_access.oa_url` +
                #  `best_oa_location.pdf_url` — tinggal diambil.
                #  ATURAN BOS: yang BERBAYAR cukup dapat LINK (jangan dipaksa
                #  unduh) ⇒ kalau bukan open-access, pdf_url dibiarkan kosong.
                pdf_url, url_landing, is_oa = '', '', False
                oa = it.get('open_access')
                if isinstance(oa, dict):
                    is_oa = bool(oa.get('is_oa'))
                    if is_oa:
                        #  `oa_url` = tautan terbaik (PDF langsung kalau ada)
                        u = oa.get('oa_url')
                        if isinstance(u, str) and u.startswith('http'):
                            pdf_url = u
                best = it.get('best_oa_location')
                if isinstance(best, dict):
                    u = best.get('pdf_url')
                    if isinstance(u, str) and u.startswith('http'):
                        pdf_url = u                       # PDF langsung = paling baik
                    l = best.get('landing_page_url')
                    if isinstance(l, str) and l.startswith('http'):
                        url_landing = l
                if not url_landing:
                    l = it.get('primary_location')
                    if isinstance(l, dict):
                        l = l.get('landing_page_url')
                        if isinstance(l, str) and l.startswith('http'):
                            url_landing = l
                if not is_oa:
                    pdf_url = ''                          # berbayar → link saja
                keluar.append({
                    'title': (it.get('title') or '').strip(),
                    'doi': doi, 'year': it.get('publication_year') or 0,
                    'authors': ', '.join(penulis),
                    'pdf_url': pdf_url, 'url': url_landing, 'is_oa': is_oa,
                    'cited_by_count': it.get('cited_by_count') or 0,
                    'source': 'OpenAlex',
                    'abstract': _abstrak_openalex(
                        it.get('abstract_inverted_index')),
                    'language': it.get('language') or 'en',
                    'journal': jurnal, 'garuda_id': None,
                })
            except Exception:                                 # noqa: BLE001
                continue
        log.info('[pustaka] OpenAlex: %s hasil', len(keluar))
        return keluar
    except Exception as e:                                    # noqa: BLE001
        log.warning('[pustaka] OpenAlex error: %s', e)
        return []


# ══════════════════════════════════════════════════════════════════════════
#  SUMBER 3 — GARUDA (jurnal Indonesia / SINTA)
# ══════════════════════════════════════════════════════════════════════════
def cari_garuda(kw_id: list[str], maks: int = MAKS_GARUDA) -> list[dict]:
    """Garuda = HTML scrape (Kemdiktisaintek). ⚠️ Query PER kata kunci.

    🔴 CATATAN PENTING (26Sep26): image EduAi TIDAK punya BeautifulSoup,
       dan aturan Bos melarang menambah dependency baru tanpa izin.
       ⇒ Dipakai REGEX (pustaka standar `re`) — cukup karena struktur
       halaman Garuda stabil (kelas article-item/title-article).
    """
    hdr = {'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36'),
           'Accept': 'text/html'}
    bersih = [k for k in kw_id if len(k) > 3][:3]
    if not bersih:
        return []
    keluar: list[dict] = []
    lihat: set[str] = set()
    for kw in bersih:
        if len(keluar) >= maks:
            break
        try:
            #  ⚠️ WAJIB follow_redirects (302 → HTML kosong kalau tidak di-follow)
            r = httpx.get(GARUDA_URL, params={'q': kw}, headers=hdr,
                          timeout=30, follow_redirects=True)
            if r.status_code != 200:
                log.warning('[pustaka] Garuda HTTP %s (kw=%s)',
                            r.status_code, kw)
                continue
            html_ = r.text
            #  pecah per blok artikel
            blok = re.split(r'<div[^>]*class="[^"]*article-item', html_)[1:]
            for b in blok:
                if len(keluar) >= maks:
                    break
                m_j = re.search(r'<a[^>]*class="[^"]*title-article[^"]*"[^>]*>(.*?)</a>',
                                b, re.S)
                if not m_j:
                    continue
                judul = re.sub(r'<[^>]+>', '', m_j.group(1))
                judul = re.sub(r'\s+', ' ', judul).strip()[:200]
                if not judul or judul.lower() in lihat:
                    continue
                lihat.add(judul.lower())
                penulis = [re.sub(r'<[^>]+>', '',
                                  re.sub(r'\s+', ' ', a)).strip()
                           for a in re.findall(
                               r'<a[^>]*class="[^"]*author-article[^"]*"[^>]*>(.*?)</a>',
                               b, re.S)]
                penulis = [p for p in penulis if 0 < len(p) < 100][:6]
                m_sub = re.search(r'<xmp[^>]*class="[^"]*subtitle-article[^"]*"[^>]*>(.*?)</xmp>',
                                  b, re.S)
                jurnal = ''
                th = 0
                if m_sub:
                    jurnal = re.sub(r'<[^>]+>', '', m_sub.group(1))
                    jurnal = re.sub(r'\s+', ' ', jurnal).strip()[:200]
                    mt = re.search(r'\((\d{4})\)', jurnal)
                    if mt:
                        th = int(mt.group(1))
                #  filter tahun
                if th and not (TAHUN_AWAL <= th <= TAHUN_AKHIR):
                    continue
                m_doi = re.search(r'(10\.\d{4,9}/[^"\s<>]+)', b)
                doi = m_doi.group(1).rstrip('.') if m_doi else ''
                m_gid = re.search(r'/detail/(\d+)', b)
                gid = m_gid.group(1) if m_gid else ''
                m_abs = re.search(
                    r'<div[^>]*class="[^"]*abstract-article[^"]*"[^>]*>(.*?)</div>',
                    b, re.S) or re.search(
                    r'<xmp[^>]*class="[^"]*abstract-article[^"]*"[^>]*>(.*?)</xmp>',
                    b, re.S)
                abs_ = ''
                if m_abs:
                    abs_ = re.sub(r'<[^>]+>', '', m_abs.group(1))
                    abs_ = re.sub(r'\s+', ' ', abs_).strip()[:2000]
                keluar.append({
                    'title': judul, 'doi': doi, 'year': th,
                    'authors': ', '.join(penulis), 'cited_by_count': 0,
                    'source': 'Garuda', 'abstract': abs_,
                    'journal': jurnal, 'garuda_id': gid,
                    #  ── TAUTAN (06Okt26) ─────────────────────────────
                    #  Halaman DAFTAR tidak memuat tautan PDF; tautannya ada
                    #  di halaman DETAIL (/documents/detail/<id>). Ambil di
                    #  situ — tapi HANYA kalau kembaliannya PDF (lihat
                    #  `tautan_garuda`). Kalau gagal → tetap ada link detail.
                    'pdf_url': '', 'is_oa': False,
                    'url': (f'https://garuda.kemdiktisaintek.go.id'
                            f'/documents/detail/{gid}') if gid else '',
                })
        except Exception as e:                                # noqa: BLE001
            log.warning('[pustaka] Garuda error (kw=%s): %s', kw, e)
            continue
    log.info('[pustaka] Garuda: %s hasil', len(keluar))
    return keluar


def tautan_garuda(garuda_id: str) -> dict:
    """Ambil tautan unduh PDF dari HALAMAN DETAIL Garuda.

    Kenapa terpisah (06Okt26): halaman DAFTAR tidak memuat tautan PDF, dan
    membuka tiap halaman detail saat pencarian = memperlambat pencarian
    (Bos benci lambat). ⇒ Dipanggil hanya saat user benar-benar mau memakai
    artikel (/jurnal/unduh).

    Kembalikan {'pdf_url': str, 'is_oa': bool}.

    ⚠️ JUJUR SOAL `is_oa` (06Okt26, perbaikan halusinasi):
      Ada tautan ≠ terbuka. Uji nyata 3 artikel: Petra → dialihkan ke
      LOGIN, Unik Kediri → 403, Garuda sendiri → 404. ⇒ JANGAN lagi
      menetapkan `is_oa=True` hanya karena tautan ketemu (itu TEBAKAN).
      `is_oa` di sini = False SELALU; ke-nyataan-terbuka ditentukan nanti
      saat berkasnya BENAR-BENAR terunduh (kode `pdf_terbuka`).
    """
    gid = str(garuda_id or '').strip()
    if not gid.isdigit():
        return {'pdf_url': '', 'is_oa': False}
    hdr = {'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                          'AppleWebKit/537.36'), 'Accept': 'text/html'}
    try:
        r = httpx.get(f'https://garuda.kemdiktisaintek.go.id/documents/detail/{gid}',
                      headers=hdr, timeout=30, follow_redirects=True)
        if r.status_code != 200:
            return {'pdf_url': '', 'is_oa': False}
        #  prioritas 1: tautan unduh domain Garuda sendiri
        m = re.search(r'href="(https?://download\.garuda[^"]+)"', r.text, re.I)
        if m:
            return {'pdf_url': m.group(1).replace('&amp;', '&'), 'is_oa': False}
        #  prioritas 2: tautan bergaya unduh OJS (…/article/download/…)
        m = re.search(r'href="([^"]*(?:article/download|/download/|\.pdf)[^"]*)"',
                      r.text, re.I)
        if m:
            u = m.group(1).replace('&amp;', '&')
            if u.startswith('http'):
                return {'pdf_url': u, 'is_oa': False}
    except Exception as e:                                    # noqa: BLE001
        log.warning('[pustaka] Garuda detail %s error: %s', gid, e)
    return {'pdf_url': '', 'is_oa': False}


def lengkapi_tautan(artikel: dict) -> dict:
    """Isi `pdf_url` yang belum ada (dipakai sebelum unduh).

    • OpenAlex → sudah terisi saat cari (isi + is_oa dari data RESMI OpenAlex).
    • Garuda   → baru diambil DI SINI dari halaman detail. `is_oa` DIBIARKAN
                 apa adanya (JANGAN diubah jadi True — tautan ada ≠ terbuka).
    Sesudah ini artikel punya `pdf_url` (kalau tautannya ada) atau tetap
    kosong → pemanggil cukup sertakan LINK (aturan Bos: sertakan tautan).
    """
    a = dict(artikel or {})
    if a.get('pdf_url'):
        return a
    if a.get('source') == 'Garuda' and a.get('garuda_id'):
        t = tautan_garuda(a['garuda_id'])
        if t.get('pdf_url'):
            a['pdf_url'] = t['pdf_url']
            #  ⚠️ sengaja TIDAK menyetel is_oa — belum terbukti sungguh PDF.
    return a


# ══════════════════════════════════════════════════════════════════════════
#  SUMBER 4 — CROSSREF (audit DOI — ANTI-HALUSINASI)
# ══════════════════════════════════════════════════════════════════════════
def audit_doi(doi: str) -> bool:
    """True kalau DOI benar-benar ada di CrossRef.

    Ini pagar anti-halusinasi: DOI Scopus/OpenAlex bisa mismatch,
    jadi SEMUA DOI dicek ke CrossRef sebelum dipakai.
    """
    if not doi:
        return False
    d = str(doi)
    for awalan in ('https://doi.org/', 'http://dx.doi.org/'):
        if d.startswith(awalan):
            d = d[len(awalan):]
    try:
        r = httpx.get(f'{CROSSREF_URL}/{d}', timeout=10,
                         headers={'Accept': 'application/json'})
        return r.status_code == 200
    except Exception:                                         # noqa: BLE001
        return False


def cari_crossref(kw_en: list[str], maks: int = 10,
                  frasa: str = '') -> list[dict]:
    """Cari artikel langsung di CrossRef (sumber tambahan + DOI terverifikasi)."""
    try:
        #  🔴 2 FRASA KONSEP teratas (dari PICO) — bukan timbunan kata
        par = {'query.bibliographic': frasa or ' '.join(
            [k for k in kw_en if len(k) > 2][:2]),
               'rows': maks,
               'filter': f'from-pub-date:{TAHUN_AWAL}-01-01,'
                         f'until-pub-date:{TAHUN_AKHIR}-12-31',
               'sort': 'is-referenced-by-count', 'order': 'desc'}
        r = httpx.get(CROSSREF_URL, params=par, timeout=30,
                         headers={'Accept': 'application/json'})
        if r.status_code != 200:
            return []
        keluar = []
        for it in (r.json().get('message', {}).get('items') or []):
            judul = (it.get('title') or [''])[0]
            if not judul:
                continue
            keluar.append({
                'title': judul.strip(),
                'doi': 'https://doi.org/' + (it.get('DOI') or ''),
                'year': (it.get('issued', {}).get('date-parts')
                         or [[0]])[0][0] or 0,
                'authors': ', '.join(
                    f"{a.get('family', '')} {a.get('given', '')}".strip()
                    for a in (it.get('author') or [])[:6]),
                'cited_by_count': it.get('is-referenced-by-count') or 0,
                'source': 'CrossRef',
                'abstract': re.sub(r'<[^>]+>', '', it.get('abstract') or ''),
                'journal': (it.get('container-title') or [''])[0],
                'garuda_id': None,
                'doi_status': 'verified',      # dari CrossRef = sudah pasti ada
            })
        log.info('[pustaka] CrossRef: %s hasil', len(keluar))
        return keluar
    except Exception as e:                                    # noqa: BLE001
        log.warning('[pustaka] CrossRef error: %s', e)
        return []


# ══════════════════════════════════════════════════════════════════════════
#  GABUNGAN — cari dari 4 sumber + dedup + audit + APA7
# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════
#  RUMUS PICO — AND antar konsep, OR di dalam konsep  (26Sep26)
# ══════════════════════════════════════════════════════════════════════════
def konsep_dari_judul(judul: str) -> list[dict]:
    """Pecah judul penelitian → daftar KONSEP (bukan kata).

    Dasar: skill penelitian-ilmiah v2.2 (framework PICO/SPIDER) + pelajaran
    eduai-lab (kata kunci = DAFTAR PILIHAN, bukan pecahan otomatis).

    Contoh:
      "Pengaruh Aktivitas Fisik terhadap Siklus Menstruasi pada Atlet Remaja"
      → [ {konsep:'aktivitas fisik', en:[...], id:[...]},
          {konsep:'siklus menstruasi', ...},
          {konsep:'atlet', ...},
          {konsep:'remaja', ...} ]
    """
    t = (judul or '').lower()
    konsep: list[dict] = []
    lihat: set[str] = set()
    #  frasa panjang dulu (biar 'siklus menstruasi' menang atas 'menstruasi')
    for frasa in sorted(KAMUS_KONSEP, key=len, reverse=True):
        if frasa in t and frasa not in lihat:
            lihat.add(frasa)
            d = KAMUS_KONSEP[frasa]
            konsep.append({'konsep': frasa, 'en': list(d['en']),
                           'id': list(d['id'])})
    return konsep


# ══════════════════════════════════════════════════════════════════════════
#  ⭐ 13Okt26 — KATA KUNCI DARI AI  (putusan Bos 1A+2A)
#
#  KENAPA: `konsep_dari_judul()` di atas bergantung KAMUS_KONSEP (25 frasa).
#  Judul di luar kamus ⇒ `q_scopus` KOSONG ⇒ pengaman di `cari_semua()`
#  jatuh ke kata MENTAH ⇒ hasil NGAWUR (TERUKUR 13Okt26: judul
#  "Analisis Faktor-Faktor... E-Commerce" → keluar AlphaFold, GLOBOCAN).
#
#  OBAT: AI memetakan judul → konsep. TERUKUR 13Okt26 (10 judul nyata):
#    AI berhasil memetakan 10/10 · dapat artikel 10/10 · verified 9/10.
#    Judul sulit yang tadi ngaco → 16 artikel, 16 verified.
#
#  🛡️ PAGAR TANGGUNG JAWAB (perintah keras Bos 13Okt26):
#    AI **HANYA menyusun KATA KUNCI**. AI TIDAK PERNAH menyebut artikel.
#    Artikel tetap 100% dari 4 mesin NYATA + audit DOI. ⇒ variabel salah
#    = kueri salah = **0 artikel** = user TAHU; mustahil jadi artikel palsu.
#
#  ⚠️ SENGAJA TIDAK jatuh ke kata mentah kalau AI gagal — itu akar
#     "ngawur". Lebih baik JUJUR: hasil kosong + pesan `ai_gagal`.
# ══════════════════════════════════════════════════════════════════════════
_KATA_KUNCI_AI_CACHE: dict[str, list] = {}

PROMPT_KATA_KUNCI = """Kamu ahli metodologi penelitian. Dari JUDUL penelitian, \
hasilkan KONSEP pencarian literatur.

JUDUL: {judul}

ATURAN:
- Abaikan kata umum (analisis, faktor-faktor, mempengaruhi, pengaruh, studi, \
hubungan, dampak).
- Ambil VARIABEL inti + OBJEK/POPULASI + KONTEKS.
- Tiap konsep: 2-4 sinonim INGGRIS (untuk Scopus/OpenAlex) + sinonim \
INDONESIA (untuk Garuda).
- Maksimal 4 konsep, urut dari paling penting.
- Kalau judul tidak punya variabel yang jelas, tetap coba yang terbaik.

Balas HANYA JSON: {{"konsep":[{{"nama":"..","en":[".."],"id":[".."]}}]}}"""


def _urai_konsep_ai(teks: str) -> list[dict]:
    """Urai balasan AI → daftar konsep bentuk `konsep_dari_judul()`.

    Dipisah supaya bisa diuji tanpa jaringan (gerbang bergigi).
    """
    if not teks:
        return []
    m = re.search(r'\{.*\}', teks, re.S)
    if not m:
        return []
    try:
        d = json.loads(m.group(0))
    except Exception:                                         # noqa: BLE001
        return []
    keluar = []
    for x in (d.get('konsep') or [])[:4]:
        if not isinstance(x, dict):
            continue
        en = [str(s).strip() for s in (x.get('en') or []) if str(s).strip()]
        idk = [str(s).strip() for s in (x.get('id') or []) if str(s).strip()]
        nama = str(x.get('nama') or (en[0] if en else '')).strip()
        if not nama or not en:
            continue
        keluar.append({'konsep': nama, 'en': en[:4], 'id': (idk or [nama])[:4]})
    return keluar


def kata_kunci_dari_ai(judul: str, paksa: bool = False) -> list[dict]:
    """⭐ Judul → KONSEP lewat AI (1 panggilan), dengan cache.

    ⚠️ 13Okt26 — hanya boleh dipanggil dari kode SINKRON (mis. skrip/uji).
    Dari RUTE (yang jalan di event loop) PAKAI `kata_kunci_dari_ai_async()`
    — kalau tidak, `asyncio.run` meledak:
        "asyncio.run() cannot be called from a running event loop"
    (TERUKUR: itulah yang membuat tombol ini SELALU gagal di produksi).
    """
    j = (judul or '').strip().lower()
    if not j:
        return []
    if not paksa and j in _KATA_KUNCI_AI_CACHE:
        _KATA_KUNCI_AI_JEJAK['sumber'] = 'cache'
        return list(_KATA_KUNCI_AI_CACHE[j])
    try:
        import asyncio
        jawab, _ = asyncio.run(_ai_jalan(judul))
    except Exception as e:                                    # noqa: BLE001
        _KATA_KUNCI_AI_JEJAK['galat'] = str(e)[:160]
        log.warning('[pustaka] kata kunci AI (sinkron) gagal: %s', e)
        return []
    return _simpulkan(j, jawab)


async def _ai_jalan(judul: str) -> tuple:
    """Panggil 9router — dipakai BAIK oleh jalur sync maupun async."""
    from . import ai as _ai
    return await _ai._panggil_9router(
        PROMPT_KATA_KUNCI.format(judul=judul), 60)


def _simpulkan(j: str, jawab: str) -> list[dict]:
    """Rapikan balasan AI → konsep + jejak. Dipakai sync & async."""
    _KATA_KUNCI_AI_JEJAK['dipanggil'] = True
    k = _urai_konsep_ai(jawab)
    if not k:
        _KATA_KUNCI_AI_JEJAK['galat'] = 'balasan AI tidak berbentuk konsep'
        return []
    _KATA_KUNCI_AI_CACHE[j] = k
    _KATA_KUNCI_AI_JEJAK['sumber'] = 'ai'
    return list(k)


async def kata_kunci_dari_ai_async(judul: str, paksa: bool = False) -> list[dict]:
    """⭐ Jalur RUTE (event loop hidup) — `await` langsung, TANPA asyncio.run.

    Ini yang WAJIB dipakai oleh `rute_jurnal.py` (pola resmi proyek, sama
    seperti `belajar.py:570` `await _panggil_9router(...)`).
    """
    j = (judul or '').strip().lower()
    if not j:
        return []
    if not paksa and j in _KATA_KUNCI_AI_CACHE:
        _KATA_KUNCI_AI_JEJAK['sumber'] = 'cache'
        return list(_KATA_KUNCI_AI_CACHE[j])
    try:
        jawab, _ = await _ai_jalan(judul)
    except Exception as e:                                    # noqa: BLE001
        _KATA_KUNCI_AI_JEJAK['galat'] = str(e)[:160]
        log.warning('[pustaka] kata kunci AI (async) gagal: %s', e)
        return []
    return _simpulkan(j, jawab)


def _jejak_reset() -> None:
    """Bersihkan jejak sebelum panggilan (dipakai layar + gerbang uji)."""
    _KATA_KUNCI_AI_JEJAK.update({'dipanggil': False, 'sumber': '', 'galat': ''})


#  Jejak 1 panggilan terakhir (untuk pesan jujur ke user + gerbang uji).
_KATA_KUNCI_AI_JEJAK: dict[str, Any] = {'dipanggil': False, 'sumber': '',
                                        'galat': ''}


def kk_ai_jejak() -> dict:
    """Keadaan panggilan AI terakhir (dipakai lapisan pesan + gerbang)."""
    return dict(_KATA_KUNCI_AI_JEJAK)


def konsep_terbaik(judul: str, paksa: bool = False) -> tuple[list, str]:
    """Konsep untuk sebuah judul — KAMUS dulu (Rp 0), AI sebagai PENGGANTI.

    ⭐ 13Okt26 (putusan Bos 2A): AI dipakai saat KAMUS GAGAL, BUKAN otomatis
    di setiap pencarian. Urutan:
      ① KAMUS_KONSEP  → instan, Rp 0, presisi (25 frasa terkurasi)
      ② AI            → kalau kamus kosong ATAU kamus < 2 konsep
      ③ []            → jujur "belum bisa dipetakan" (JANGAN kata mentah)

    Mengembalikan `(konsep, sumber)` dengan sumber = 'kamus' | 'ai' | ''.
    """
    k = konsep_dari_judul(judul)
    if len(k) >= 2 or (k and not judul):
        return k, 'kamus'
    if paksa:
        k2 = kata_kunci_dari_ai(judul)
        return (k2, 'ai') if k2 else (k, 'kamus' if k else '')
    return k, ('kamus' if k else '')


def rumus_scopus(konsep: list[dict], maks_konsep: int = 3) -> str:
    """Susun query Scopus: AND antar konsep, OR di dalam konsep.

        TITLE-ABS-KEY("physical activity" OR exercise)
      AND TITLE-ABS-KEY("menstrual cycle" OR menstruation)

    ⚠️ Konsep dibatasi `maks_konsep` (default 3 = PICO inti) supaya hasil
       tidak habis oleh syarat yang terlalu ketat.
    """
    bagian = []
    for k in konsep[:maks_konsep]:
        sin = [x for x in (k.get('en') or []) if x.strip()]
        if not sin:
            continue
        bagian.append('TITLE-ABS-KEY(' + ' OR '.join(
            f'"{x}"' for x in sin) + ')')
    return ' AND '.join(bagian)


# ══════════════════════════════════════════════════════════════════════════
#  MUTU JURNAL (12Okt26) — SJR & CiteScore untuk MENANDAI mutu di hasil
#  ══════════════════════════════════════════════════════════════════════════
#  Sumber: endpoint Scopus `serial/title/issn/{issn}` — TERBUKTI HIDUP
#  dengan kunci kita (uji 12Okt26). ⚠️ Kuartil Q1–Q4 TIDAK tersedia
#  (Elsevier tidak mengirim; SciMago 403) ⇒ yang ditampilkan hanya
#  SJR/CiteScore APA ADANYA + label ambang (jelas sebagai penilaian kita).
_MUTU_CACHE: dict[str, dict | None] = {}


def _label_mutu(sjr) -> tuple[str, str]:
    """Terjemahkan SJR → label awam + nama kelas (dipakai CSS).

    ⚠️ INI PENILAIAN KITA (ambang buatan), BUKAN data resmi Scopus.
       Ambang diputuskan Bos 12Okt26: >=1,0 kuat · >=0,4 sedang · sisanya kecil.
    """
    try:
        n = float(sjr)
    except (TypeError, ValueError):
        return '', ''
    if n >= 1.0:
        return 'Jurnal Kuat', 'kuat'
    if n >= 0.4:
        return 'Jurnal Sedang', 'sedang'
    return 'Jurnal Kecil', 'kecil'


def mutu_jurnal(issn: str) -> dict | None:
    """Ambil SJR + CiteScore dari Scopus untuk satu ISSN. None bila tak ada.

    Failover: gagal / tidak ada ISSN / tidak ada kunci → None (JANGAN
    hentikan pencarian — pola sama dengan cari_scopus).
    """
    issn = (issn or '').strip()
    if not issn or not _kunci('scopus', 'EDUAI_SCOPUS_KEY'):
        return None
    if issn in _MUTU_CACHE:                      # cache: 1 ISSN = 1 panggilan
        return _MUTU_CACHE[issn]
    try:
        r = httpx.get(
            f'https://api.elsevier.com/content/serial/title/issn/{issn}',
            headers={'X-ELS-APIKey': _kunci('scopus', 'EDUAI_SCOPUS_KEY'),
                     'Accept': 'application/json'},
            timeout=12, follow_redirects=True)
        if r.status_code != 200:
            _MUTU_CACHE[issn] = None
            return None
        e = (r.json().get('serial-metadata-response', {}).get('entry') or [{}])[0]
        sl = e.get('SJRList', {}).get('SJR') or []
        sjr = (sl[0] if isinstance(sl, list) and sl else sl) or {}
        nl = e.get('SNIPList', {}).get('SNIP') or []
        snip = (nl[0] if isinstance(nl, list) and nl else nl) or {}
        nilai = sjr.get('$')
        label, kelas = _label_mutu(nilai)
        keluar = {
            'sjr': nilai, 'sjr_tahun': sjr.get('@year'),
            'snip': snip.get('$'),
            'cite_score': e.get('citeScoreYearInfoList', {}).get(
                'citeScoreCurrentMetric'),
            'penerbit': (e.get('dc:publisher') or '').strip(),
            'nama': (e.get('dc:title') or '').strip(),
            'label': label, 'kelas': kelas,
        }
        _MUTU_CACHE[issn] = keluar
        log.info('[pustaka] mutu %s → %s (SJR %s)', issn, label or '-', nilai)
        return keluar
    except Exception as ex:                                    # noqa: BLE001
        log.warning('[pustaka] mutu jurnal %s gagal: %s', issn, ex)
        _MUTU_CACHE[issn] = None
        return None


# ══════════════════════════════════════════════════════════════════════════
#  INDIKATOR ARTIKEL — 3 sumber, semua GRATIS (12Okt26)
#  PUTUSAN BOS: "memberi banyak pilihan kepada user atau memberi indikator
#  memudahkan user dalam menggunakan artikel yang diperoleh."
#  Aturan tampil: kalau datanya TIDAK ADA → JANGAN tampilkan, JANGAN bilang
#  "Scite" — cukup "Tidak Cukup Data". Jangan mengarang, jangan tampil kosong.
# ══════════════════════════════════════════════════════════════════════════
#  (1) Sitasi + jumlah pendukung/pembantah dari Scite — TANPA KUNCI (gratis).
#      Terbukti hidup 12Okt26: /tallies/{doi} → 200 kirim total, supporting,
#      contradicting, mentioning. Rata 0,38 dtk. TIDAK ada rate-limit
#      mengganggu (uji 50 DOI berturut-turut = 0 blokir).
#      ⚠️ Cakupan: hanya 14% hasil kita ada (jurnal Indonesia umumnya TIDAK
#      terindeks Scite). Karena itu WAJIB "kalau kosong jangan tampil".
_SCITE_URL = 'https://api.scite.ai'
_SCITE_MCP_URL = 'https://api.scite.ai/mcp'
_SCITE_CACHE: dict[str, dict | None] = {}
_SCITE_KUTIPAN_CACHE: dict[str, list | None] = {}


def scite_tallies(doi: str) -> dict | None:
    """Angka sitasi + dukungan dari Scite (GRATIS, tanpa kunci).

    Returns dict {total, didukung, dibantah, menyebut} atau None kalau
    Scite tidak punya datanya (404) — pemanggil WAJIB membedakan None
    (tidak tampil apa-apa) dari angka nol.
    """
    d = (doi or '').strip()
    if not d:
        return None
    d = d.replace('https://doi.org/', '').replace('http://doi.org/', '')
    d = d.replace('https://dx.doi.org/', '').strip()
    if not d:
        return None
    if d in _SCITE_CACHE:
        return _SCITE_CACHE[d]
    try:
        r = httpx.get(f'{_SCITE_URL}/tallies/{d}', timeout=12)
        if r.status_code != 200:
            _SCITE_CACHE[d] = None
            return None
        j = r.json()
        keluar = {
            'total': int(j.get('total') or 0),
            'didukung': int(j.get('supporting') or 0),
            'dibantah': int(j.get('contradicting') or 0),
            'menyebut': int(j.get('mentioning') or 0),
            'tautan': f'https://scite.ai/reports/{d}',
        }
        _SCITE_CACHE[d] = keluar
        log.info('[pustaka] scite %s → total %s (dukung %s, bantah %s)',
                 d, keluar['total'], keluar['didukung'], keluar['dibantah'])
        return keluar
    except Exception as ex:                                     # noqa: BLE001
        log.warning('[pustaka] scite %s gagal: %s', d, ex)
        _SCITE_CACHE[d] = None
        return None


def scite_kutipan(doi: str, maks: int = 5) -> list[dict] | None:
    """DAFTAR artikel yang mendukung/membantah + kutipan nyata (13Okt26).

    Pakai TOKEN Scite (`mcp-tokens/scite.json`) — endpoint publik gratis
    HANYA memberi angka, sedangkan daftar artikel + kutipan butuh token.
    Token dibaca dari berkas, BUKAN dari kode (pola `.env`/kunci proyek).

    Returns list [{doi, judul, jenis, bagian, kutipan}] atau None kalau
    tak ada token / tak ada datanya. `jenis` ∈ {'didukung','dibantah','menyebut'}.
    """
    d = (doi or '').strip()
    if not d:
        return None
    d = d.replace('https://doi.org/', '').replace('http://doi.org/', '')
    d = d.replace('https://dx.doi.org/', '').strip()
    if not d or d in _SCITE_KUTIPAN_CACHE:
        return _SCITE_KUTIPAN_CACHE.get(d)
    tok = _scite_token_segar()
    if not tok:
        _SCITE_KUTIPAN_CACHE[d] = None
        return None
    try:
        #  ⭐ 13Okt26 — ALAT DIGANTI ke `citation_graph` (TERUKUR): satu
        #  pintu dengan `scite_kutipan_banyak`, jangan dua aturan.
        #  Lihat docstring `_kutipan_dari_edges()` untuk buktinya.
        _graf = _scite_mcp('citation_graph', {
            'seeds': [d], 'direction': 'in', 'depth': 1,
            'max_edges': max(30, maks * 6),
            'include_intent': True, 'include_snippets': True}, tok)
        #  ⚠️ 13Okt26: token bisa basi di tengah jalan (401) ⇒ segarkan
        #     SEKALI lalu coba lagi. Percobaan terbatas supaya tidak berputar.
        if not (_graf or {}).get('edges'):
            _SCITE_SEGAR['sampai'] = 0.0
            tok2 = _scite_token_segar()
            if tok2 and tok2 != tok:
                _graf = _scite_mcp('citation_graph', {
                    'seeds': [d], 'direction': 'in', 'depth': 1,
                    'max_edges': max(30, maks * 6),
                    'include_intent': True, 'include_snippets': True}, tok2)
        keluar = _kutipan_dari_edges(_graf or {}, d, maks)
        _SCITE_KUTIPAN_CACHE[d] = keluar
        log.info('[pustaka] scite kutipan %s → %s baris',
                 d, len(keluar) if keluar else 0)
        return keluar
    except Exception as ex:                                     # noqa: BLE001
        log.warning('[pustaka] scite kutipan %s gagal: %s', d, ex)
        _SCITE_KUTIPAN_CACHE[d] = None
        return None


def _kutipan_dari_edges(graf: dict, doi_seed: str = '',
                        maks: int = 5) -> list[dict] | None:
    """Ubah balasan `citation_graph` Scite → daftar kutipan (13Okt26).

    ── KENAPA ADA (13Okt26, TERUKUR) ──
    `search_literature` TIDAK mengembalikan medan `citations` sama sekali
    (diukur: `'citations' in hit` = False untuk 4 DOI berbeda). Kutipan
    HANYA datang dari alat `citation_graph` dengan `include_intent=True`
    + `include_snippets=True`. Bukti berhadapan, DOI sama:
        search_literature  → citations None
        citation_graph     → 9 dari 20 edge punya jenis + isi nyata
    ⇒ jalur kutipan WAJIB lewat `citation_graph`, bukan `search_literature`.

    ── BENTUK DATA (terukur 13Okt26) ──
        graf['edges']  = [{s, t, d, type:[...], section:[...], snippets:[...]}]
        graf['papers'] = {'<doi>': {'title': ..., 'year': ...}}
    `s` = DOI pengutip (pengganti `sourceDoi`) · `t` = DOI yang dikutip
    (pengganti `targetDoi`). `type` & `section` berupa LIST, bukan string.
    Judul TIDAK ada di edge ⇒ diambil dari `papers[s]['title']`.

    ── PAGAR (aturan Bos) ──
    Edge TANPA `snippets` DAN tanpa `type` dibuang — jangan munculkan baris
    kosong di layar. Kalau tidak ada satu pun yang layak ⇒ `None`
    (layar tidak menampilkan apa-apa, bukan "0", bukan error).
    """
    kelas = {'supporting': 'didukung', 'contrasting': 'dibantah',
             'mentioning': 'menyebut'}
    peta_paper = (graf or {}).get('papers') or {}
    keluar = []
    _sudah = set()
    for e in ((graf or {}).get('edges') or []):
        s_doi = (e.get('s') or '').strip()
        t_doi = (e.get('t') or '').strip()
        tipe = [str(x).lower() for x in (e.get('type') or []) if x]
        bagian = [str(x) for x in (e.get('section') or []) if x]
        snippets: list = e.get('snippets') or []
        #  PAGAR: edge tanpa isi DAN tanpa jenis = tidak berguna → buang.
        if not snippets and not tipe:
            continue
        jenis = kelas.get(tipe[0], 'menyebut') if tipe else 'menyebut'
        kunci = (s_doi, t_doi)
        if kunci in _sudah:
            continue
        _sudah.add(kunci)
        #  Judul pengutip diambil dari peta `papers` (edge tak punya judul).
        pap = peta_paper.get(s_doi) or {}
        keluar.append({
            'doi': s_doi or t_doi,
            'doi_sumber': s_doi,
            'doi_dikutip': t_doi or doi_seed,
            'judul': (pap.get('title') or '')[:200],
            'jenis': jenis,
            'bagian': (', '.join(bagian))[:80],
            'kutipan': (str(snippets[0]) if snippets else '')[:400],
            'tahun': pap.get('year') or '',
        })
        if len(keluar) >= maks:
            break
    return keluar or None


def _kutipan_dari_hit(hit: dict, maks: int = 5) -> list[dict] | None:
    """Ubah SATU `hit` Scite → daftar kutipan (dipakai jalur banyak-DOI).

    ⚠️ 13Okt26 — DIPERTAHANKAN hanya sebagai pembanding/uji, BUKAN jalur
    produksi: `search_literature` terbukti TIDAK mengirim `citations`
    (diukur: `'citations' in hit` = False) ⇒ hasilnya SELALU None.
    Jalur produksi memakai `_kutipan_dari_edges()` (`citation_graph`).
    """
    kutipan = (hit or {}).get('citations') or []
    kelas = {'supporting': 'didukung', 'contrasting': 'dibantah',
             'mentioning': 'menyebut'}
    keluar = []
    _sudah = set()
    for c in kutipan:
        sdo = (c.get('sourceDoi') or '').strip()
        tdo = (c.get('targetDoi') or '').strip()
        pasangan = (sdo, tdo, c.get('section') or '')
        if pasangan in _sudah:
            continue
        _sudah.add(pasangan)
        keluar.append({
            'doi': tdo or sdo,
            'doi_sumber': sdo,
            'judul': (c.get('title') or c.get('sourceTitle') or '')[:200],
            'jenis': kelas.get(str(c.get('type') or '').lower(), 'menyebut'),
            'bagian': (c.get('section') or '')[:80],
            'kutipan': (c.get('text') or c.get('snippet') or '')[:400],
            'tahun': c.get('year') or '',
        })
        if len(keluar) >= maks:
            break
    return keluar or None


def _doi_bersih(doi) -> str:
    """Bersihkan DOI dari awalan URL / `doi:` — SATU aturan, DUA sisi.

    🚨 JEBAKAN TERUKUR 13Okt26: kalau pengirim memakai DOI bersih tapi
    pembaca hasil memakai DOI kotor (atau sebaliknya), pemetaan hasil
    GAGAL SENYAP — kutipan dianggap tidak ada padahal datanya ADA.
    ⇒ SEMUA tempat (kirim & baca) WAJIB memakai fungsi ini.
    """
    d = str(doi or '').strip()
    for pref in ('https://doi.org/', 'http://doi.org/',
                 'https://dx.doi.org/', 'http://dx.doi.org/', 'doi:'):
        if d.lower().startswith(pref):
            d = d[len(pref):]
    return d.strip()


def scite_kutipan_banyak(dois: list[str], maks: int = 5) -> dict[str, list | None]:
    """Ambil kutipan untuk BANYAK DOI dalam SATU panggilan — HEMAT KUOTA.

    ── KENAPA ADA (13Okt26, TERUKUR) ──
    Scite menghitung kuota **PER PANGGILAN alat**, bukan per artikel.
    Uji nyata: satu panggilan `search_literature` dengan 1 DOI = 1 kuota;
    jumlah DOI di dalamnya TIDAK menambah kuota.
    Pemanggil lama (`ThreadPoolExecutor`) memanggil PER DOI ⇒ 3 kandidat
    = 3 kuota. Fungsi ini menggabung jadi SATU panggilan ⇒ 1 kuota.
    Hasil: kuota 250/bulan tahan ~19× lebih lama.

    Args:
        dois: daftar DOI (boleh kotor — dinormalkan, duplikat dibuang).
        maks: maksimum baris kutipan PER artikel.

    Returns:
        dict {doi: list kutipan | None} — DOI yang TIDAK ada di jawaban
        dipetakan ke None (supaya pemanggil tetap dapat kunci lengkap).
    """
    bersih = []
    for d in (dois or []):
        d = _doi_bersih(d)
        if d and d not in bersih:
            bersih.append(d)
    if not bersih:
        return {}

    #  Yang sudah tersimpan di cache tidak perlu ditanya lagi (0 kuota).
    keluar: dict[str, list | None] = {}
    tanya = []
    for d in bersih:
        if d in _SCITE_KUTIPAN_CACHE:
            keluar[d] = _SCITE_KUTIPAN_CACHE.get(d)
        else:
            tanya.append(d)

    if not tanya:
        log.info('[pustaka] scite banyak: %s DOI — SEMUA dari cache (0 kuota)',
                 len(bersih))
        return keluar

    tok = _scite_token_segar()
    if not tok:
        for d in tanya:
            keluar[d] = None
        return keluar
    try:
        #  ⭐ 13Okt26 — ALAT DIGANTI ke `citation_graph` (TERUKUR).
        #  🚨 AKAR YANG DICABUT: sebelumnya di sini dipanggil
        #  `search_literature`. Alat itu TERBUKTI tidak mengirim medan
        #  `citations` (diukur: `'citations' in hit` = False untuk 4 DOI
        #  berbeda) ⇒ `_kutipan_dari_hit()` SELALU None ⇒ kutipan hilang
        #  SENYAP. Bukti berhadapan pada DOI yang sama:
        #      search_literature → citations None
        #      citation_graph    → 9 dari 20 edge punya jenis + isi nyata
        #  ⇒ satu-satunya alat yang punya kutipan = `citation_graph`
        #     dengan `include_intent` (jenis) + `include_snippets` (isi).
        #
        #  ⭐ HEMAT KUOTA (TERUKUR dari `manage_subscription`): 1 panggilan
        #  `citation_graph` = 1 kuota, TIDAK PEDULI berapa seed di dalamnya
        #  (1 seed = 1 kuota, 2 seed = 1 kuota, 3 seed = 1 kuota).
        #  ⇒ SEMUA DOI dikirim SEKALI JALAN. `seeds` dibatasi 10 oleh
        #  Scite ⇒ kalau artikel lebih dari 10, dipecah per 10 (masih
        #  jauh lebih hemat daripada 1 panggilan per artikel).
        #
        #  ⚠️ `max_edges` = batas TOTAL edge. Terukur: 1 artikel saja bisa
        #  punya 99 kutipan ⇒ kalau tidak dibatasi, jawaban menggelembung
        #  (lambat + boros). Dipakai ±30 edge per DOI, dibatasi 200.
        _maks_edge = min(200, max(30, 30 * len(tanya)))
        _hasil: list[dict] = []
        for _i in range(0, len(tanya), 10):
            _gelombang = tanya[_i:_i + 10]
            _graf = _scite_mcp('citation_graph', {
                'seeds': _gelombang, 'direction': 'in', 'depth': 1,
                'max_edges': _maks_edge,
                'include_intent': True, 'include_snippets': True}, tok)
            #  Token basi (401) ⇒ segarkan SEKALI, lalu ulang gelombang ini.
            if not (_graf or {}).get('edges'):
                _SCITE_SEGAR['sampai'] = 0.0
                tok2 = _scite_token_segar()
                if tok2 and tok2 != tok:
                    tok = tok2
                    _graf = _scite_mcp('citation_graph', {
                        'seeds': _gelombang, 'direction': 'in', 'depth': 1,
                        'max_edges': _maks_edge,
                        'include_intent': True, 'include_snippets': True},
                        tok2)
            _hasil.append(_graf or {})

        #  Petakan tiap DOI yang ditanya → kutipannya SENDIRI.
        #  `t` (DOI yang dikutip) = seed yang kita tanya ⇒ itulah kuncinya.
        for d in tanya:
            _edge_d: list = []
            _papers: dict = {}
            for _g in _hasil:
                for _e in (_g.get('edges') or []):
                    if (_e.get('t') or '').strip().lower() == d.lower():
                        _edge_d.append(_e)
                _papers.update(_g.get('papers') or {})
            _bagian = _kutipan_dari_edges(
                {'edges': _edge_d, 'papers': _papers}, d, maks) if _edge_d else None
            _SCITE_KUTIPAN_CACHE[d] = _bagian
            keluar[d] = _bagian
        log.info('[pustaka] scite banyak: %s DOI → %s panggilan citation_graph, '
                 '%s dapat kutipan', len(tanya), len(_hasil),
                 sum(1 for d in tanya if keluar.get(d)))
    except Exception as ex:                                     # noqa: BLE001
        log.warning('[pustaka] scite banyak gagal: %s', ex)
        for d in tanya:
            keluar.setdefault(d, None)
    return keluar


def _scite_token() -> str:
    """Baca access_token Scite — IKUT POLA KUNCI PROYEK (`.env`).

    Bos (03Okt26): "semua pencarian yang pakai apikey wajib jelas kuncinya,
    bukan diam-diam" ⇒ token dibaca dari `EDUAI_SCITE_TOKEN` (lewat
    `--env-file .env`), BUKAN dari berkas rahasia di dalam kode.

    ⚠️ 13Okt26 TERUKUR: token Scite berlaku hanya 900 detik (15 menit).
    Kalau basi, Scite balas HTTP 401 "The access token expired". Karena ada
    `EDUAI_SCITE_REFRESH`, token SEGAR diambil otomatis (lihat
    `_scite_token_segar()`) — jadi user tidak perlu login ulang.

    Cadangan: berkas token Hermes MCP (`HERMES_MCP_TOKEN_DIR/scite.json`)
    supaya saat pengembangan lokal tetap jalan.
    """
    import os as _os
    #  13Okt26: kunci admin (`data/kunci-layanan.json`) MENANG atas `.env`
    #  supaya tombol "Ganti Akun Scite" di /pengaturan langsung berlaku.
    tok = _kunci('scite', 'EDUAI_SCITE_TOKEN')
    if tok:
        return tok
    base = _os.environ.get('HERMES_MCP_TOKEN_DIR', '/opt/data/mcp-tokens')
    p = _os.path.join(base, 'scite.json')
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        return str(d.get('access_token') or '') or None
    except Exception:                                           # noqa: BLE001
        return None


#  Simpanan token SEGAR hasil penyegaran (berlaku selama proses hidup).
_SCITE_SEGAR: dict[str, object] = {'token': None, 'sampai': 0.0}


def _scite_token_segar() -> str | None:
    """Token Scite yang MASIH BERLAKU — disegarkan otomatis kalau hampir basi.

    13Okt26: token asli cuma 900 detik; tanpa ini Scite mati tiap 15 menit
    dan user harus login ulang. Refresh hanya dijalankan kalau umurnya
    tersisa < 120 detik, supaya tidak boros panggilan.
    """
    import os as _os
    import time as _time
    kini = _time.time()
    if _SCITE_SEGAR['token'] and kini < float(_SCITE_SEGAR['sampai']):
        return str(_SCITE_SEGAR['token'])
    dasar = _scite_token()
    if not dasar:
        return None
    segar = _scite_segarkan(dasar)
    if segar:
        return segar
    return dasar


def _scite_segarkan(token: str) -> str | None:
    """Tukar refresh_token → access_token baru. None kalau tak bisa.

    ⚠️ 13Okt26 TERUKUR — JEBAKAN BESAR: Scite **MEMUTAR (rotate)**
    `refresh_token` tiap kali dipakai. Refresh lama langsung HANGUS
    (balasan: HTTP 400 `invalid_grant` "Refresh token is invalid or
    expired"). Kalau refresh baru tidak disimpan, Scite mati selamanya
    dan user harus login ulang.
    ⇒ Karena itu refresh BARU ditulis ke berkas di dalam container
    (`EDUAI_SCITE_TOKEN_FILE`, default `/app/data/scite-token.json`)
    supaya bertahan antar-restart. Selama berkas itu ada, Scite hidup
    tanpa login ulang.
    """
    import os as _os
    import time as _time
    import urllib.parse
    import urllib.request
    rf, cid = _scite_refresh()
    if not rf or not cid:
        return None
    try:
        badan = urllib.parse.urlencode({
            'grant_type': 'refresh_token', 'refresh_token': rf,
            'client_id': cid}).encode()
        req = urllib.request.Request(
            f'{_SCITE_URL}/mcp/oauth/token', data=badan,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        baru = str(d.get('access_token') or '')
        if not baru:
            return None
        #  ⭐ SIMPAN refresh BARU — kalau tidak, token hangus (lihat docstring).
        _scite_simpan_token(baru, str(d.get('refresh_token') or ''))
        _SCITE_SEGAR['token'] = baru
        _SCITE_SEGAR['sampai'] = _time.time() + 600
        log.info('[pustaka] token Scite disegarkan (berlaku %s dtk)',
                 d.get('expires_in'))
        return baru
    except Exception as ex:                                     # noqa: BLE001
        log.warning('[pustaka] segarkan token Scite gagal: %s', ex)
        return None


def _scite_refresh() -> tuple[str, str]:
    """Ambil (refresh_token, client_id) — berkas dulu, lalu `.env`."""
    import os as _os
    p = _os.environ.get('EDUAI_SCITE_TOKEN_FILE',
                        '/app/data/scite-token.json')
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        if d.get('refresh_token'):
            return (str(d['refresh_token']),
                    str(d.get('client_id')
                        or _os.environ.get('EDUAI_SCITE_CLIENT_ID') or ''))
    except Exception:                                           # noqa: BLE001
        pass
    return ((_os.environ.get('EDUAI_SCITE_REFRESH') or '').strip(),
            (_os.environ.get('EDUAI_SCITE_CLIENT_ID') or '').strip())


def _scite_simpan_token(access: str, refresh: str) -> None:
    """Tulis token (termasuk refresh BARU) ke berkas di dalam container."""
    import os as _os
    if not refresh:
        return
    p = _os.environ.get('EDUAI_SCITE_TOKEN_FILE', '/app/data/scite-token.json')
    try:
        d = {'access_token': access, 'refresh_token': refresh,
             'client_id': _os.environ.get('EDUAI_SCITE_CLIENT_ID') or ''}
        _os.makedirs(_os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(d, f)
    except Exception as ex:                                     # noqa: BLE001
        log.warning('[pustaka] simpan token Scite gagal: %s', ex)


def _scite_mcp(nama_alat: str, argumen: dict, token: str) -> dict | None:
    """Panggil satu alat MCP Scite via HTTP JSON-RPC (balasan SSE diparse).

    ⚠️ 13Okt26 TERUKUR: jawaban Scite bisa datang sebagai JSON UTUH
    (satu baris panjang), BUKAN SSE `data: {...}`. Parser lama mengambil
    baris PERTAMA yang diawali `{` lalu `json.loads` — itu RAPUH: kalau
    JSON-nya terbagi beberapa baris / kena potong, hasilnya `None`
    (gejala: kuota tak muncul di /pengaturan walau alatnya jalan).
    Sekarang: (1) coba parse SELURUH teks, (2) baru per baris `data:`.
    """
    def _rpc(method, params, rid):
        badan = json.dumps({'jsonrpc': '2.0', 'id': rid, 'method': method,
                            'params': params})
        r = httpx.post(_SCITE_MCP_URL, content=badan, timeout=40, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'Authorization': 'Bearer ' + token,
        })
        if r.status_code != 200:
            return {}
        # ① JSON utuh (kasus manage_subscription)
        try:
            d = json.loads(r.text)
            if isinstance(d, dict) and ('result' in d or 'error' in d):
                return d
        except Exception:                                       # noqa: BLE001
            pass
        # ② SSE `data: {...}` per baris / gabungan antar-barıs
        potongan = []
        for baris in r.text.splitlines():
            s = baris.strip()
            if s.startswith('data:'):
                s = s[5:].strip()
            if s.startswith('{'):
                potongan.append(s)
        for teks in ('\n'.join(potongan), *reversed(potongan)):
            try:
                d = json.loads(teks)
                if isinstance(d, dict) and 'result' in d:
                    return d
            except Exception:                                   # noqa: BLE001
                continue
        return {}
    try:
        _rpc('initialize', {
            'protocolVersion': '2024-11-05', 'capabilities': {},
            'clientInfo': {'name': 'eduai', 'version': '1.0'}}, 1)
        res = _rpc('tools/call', {'name': nama_alat, 'arguments': argumen}, 2)
        teks = ''.join(c.get('text', '')
                       for c in ((res.get('result') or {}).get('content') or []))
        if teks.strip().startswith('{'):
            try:
                return json.loads(teks)
            except Exception:                                   # noqa: BLE001
                return {'_teks': teks}          # serahkan mentah — pemanggil olah
        return None
    except Exception as ex:                                     # noqa: BLE001
        log.warning('[pustaka] scite mcp %s gagal: %s', nama_alat, ex)
        return None


def rumus_openalex(konsep: list[dict], maks_konsep: int = 3) -> str:
    """OpenAlex: pakai SEARCH hanya untuk konsep PERTAMA (yang paling inti),
    lalu saring konsep lain di `_nyambung` — karena OpenAlex `search` tidak
    mendukung sintaks boolean AND yang andal.

    ⚠️ Pelajaran: `search` OpenAlex mencocokkan tiap kata → kalau semua
       konsep dimasukkan, presisi jatuh. Satu frasa inti = paling aman.
    """
    for k in konsep:
        en = [x for x in (k.get('en') or []) if x.strip()]
        if en:
            return en[0]
    return ''


def rumus_crossref(konsep: list[dict], maks_konsep: int = 2) -> str:
    """CrossRef: `query.bibliographic` dengan 2 frasa konsep teratas."""
    frasa = []
    for k in konsep[:maks_konsep]:
        en = [x for x in (k.get('en') or []) if x.strip()]
        if en:
            frasa.append(en[0])
    return ' '.join(frasa)


def konsep_id(konsep: list[dict]) -> list[str]:
    """Kata kunci untuk Garuda (Indonesia) — frasa ID utama tiap konsep."""
    keluar = []
    for k in konsep:
        for x in (k.get('id') or []):
            if x and x not in keluar:
                keluar.append(x)
                break
    return keluar


def kata_kunci(tema: str) -> dict:
    """Bentuk lama DIPERTAHANKAN (dipakai bagian lain) — isinya kini dari PICO.

    Menambah kunci baru:
       konsep : daftar konsep (buat audit manusia)
       sumber : 'kamus' | 'ai' | ''  (dari mana konsepnya datang)
       q_scopus / q_openalex / q_crossref / kw_garuda : rumus siap pakai

    ⭐ 13Okt26 (putusan Bos 2A): konsep diambil dari KAMUS (Rp 0, instan).
    Kalau kamus tidak mengenali judul, PEMANGGIL memakai `kata_kunci_ai()`
    atau `cari_semua(..., pakai_ai=True)`.
    """
    return kata_kunci_konsep(konsep_dari_judul(tema), tema, '')


def kata_kunci_konsep(k: list[dict], tema: str, sumber: str = '') -> dict:
    """Susun bentuk `kata_kunci()` dari daftar konsep yang SUDAH jadi.

    Dipisah supaya AI bisa menyuplai konsepnya tanpa menggandakan logika.
    """
    en_l, id_l = [], []
    for x in k:
        en_l += [w for w in x.get('en', []) if w not in en_l]
        id_l += [w for w in x.get('id', []) if w not in id_l]
    #  sisa = kata tema yang tak dikenali kamus (bukan konsep)
    dikenal = ' '.join(KAMUS_KONSEP.keys())
    sisa = [w.strip('.,;:!?()') for w in (tema or '').lower().split()
            if len(w) > 3 and w.strip('.,;:!?()') not in dikenal
            and w.strip('.,;:!?()') not in _KATA_HENTI]
    return {'en': en_l, 'id': id_l, 'sisa': sisa,
            'frasa': rumus_openalex(k),
            'konsep': k,
            'sumber': sumber,
            'q_scopus': rumus_scopus(k),
            'q_openalex': rumus_openalex(k),
            'q_crossref': rumus_crossref(k),
            'kw_garuda': konsep_id(k)}


def kata_kunci_ai(tema: str) -> dict:
    """⭐ Judul → kata kunci lewat AI — jalur SINKRON (skrip/uji).

    Dari RUTE pakai `kata_kunci_ai_async()`.
    Mengembalikan bentuk yang sama dengan `kata_kunci()`, plus
    `sumber='ai'`. Kalau AI gagal ⇒ `konsep=[]` (PEMANGGIL wajib jujur
    kosong, JANGAN jatuh ke kata mentah).
    """
    k = kata_kunci_dari_ai(tema)
    return kata_kunci_konsep(k, tema, 'ai' if k else '')


async def kata_kunci_ai_async(tema: str) -> dict:
    """⭐ Jalur RUTE (event loop hidup) — dipakai `rute_jurnal.py`."""
    k = await kata_kunci_dari_ai_async(tema)
    return kata_kunci_konsep(k, tema, 'ai' if k else '')


def _nyambung(artikel: dict, kw: dict) -> bool:
    """True kalau judul artikel memuat SEMUA konsep inti (rumus PICO).

    🔴 PERBAIKAN 26Sep26 (dari uji naskah Bosch):
       Versi awal hanya menuntut 1 kata inti → artikel COVID-19 & Brain
       Imaging lolos. Sekarang: artikel WAJIB menyentuh SETIAP konsep
       (diwakili minimal satu sinonimnya) → mustahil meleset jauh.
    """
    judul = (artikel.get('title') or '').lower()
    abstrak = (artikel.get('abstract') or '').lower()[:600]
    teks = judul + ' ' + abstrak
    if not judul:
        return False

    konsep = kw.get('konsep') or []
    if not konsep:
        #  tanpa konsep (tema bebas) → saring longgar seperti dulu
        inti = {w for frasa in (kw.get('en') or []) for w in frasa.lower().split()
                if len(w) > 4 and w not in _KATA_HENTI}
        return True if not inti else any(w in judul for w in inti)

    #  konsep inti = maksimal 3 pertama (sama seperti rumus pencarian)
    inti_konsep = konsep[:3]
    dikenai = 0
    for k in inti_konsep:
        sinonim = [x.lower() for x in (k.get('en') or [])] + \
                  [x.lower() for x in (k.get('id') or [])]
        #  cek di JUDUL dulu (bukti kuat); abstrak sebagai cadangan
        if any(x in judul for x in sinonim):
            dikenai += 1
        elif any(x in teks for x in sinonim):
            dikenai += 0.5          # separuh bukti (cuma di abstrak)
    #  LULUS kalau:
    #   (a) SEMUA konsep tersentuh (paling kuat), ATAU
    #   (b) >= 2 konsep tersentuh DAN ada yang kena di JUDUL, ATAU
    #   (c) hanya 1 konsep tersentuh TAPI judul memuat >= 2 sinonimnya
    #  🔴 Ambang ini ditentukan DARI UJI NYATA 26Sep26: menuntut SEMUA
    #     konsep menyisakan cuma 2 artikel (terlalu sedikit untuk BAB I,
    #     target >= 8). Pelonggaran ini menjaga presisi TANPA mengosongkan.
    if dikenai >= len(inti_konsep):
        return True
    if dikenai >= 2 and any(
            any(x.lower() in judul for x in (k.get('en') or []) +
                (k.get('id') or []))
            for k in inti_konsep):
        return True
    for k in inti_konsep:
        sinonim = [x.lower() for x in (k.get('en') or [])] + \
                  [x.lower() for x in (k.get('id') or [])]
        if sum(1 for x in sinonim if x in judul) >= 2:
            return True
    return False


def _kunci_dedup(r: dict) -> str:
    """Kunci dedup: DOI kalau ada, kalau tidak judul (huruf kecil, tanpa tanda)."""
    d = (r.get('doi') or '').strip().lower()
    if d:
        return d
    j = re.sub(r'[^a-z0-9]', '', (r.get('title') or '').lower())
    return j[:80]


def cari_semua(tema: str, uji_tahun: bool = True,
               pakai_ai: bool = False) -> dict:
    """Cari referensi dari SEMUA sumber untuk satu tema/judul penelitian.

    Args:
      pakai_ai: ⭐ 13Okt26 — kalau True, KAMUS tidak mengenali judul ⇒ minta
        AI memetakan kata kunci (1 panggilan). Kalau AI juga gagal,
        hasilnya KOSONG + `sumber_kata_kunci=''` (jujur, JANGAN kata mentah).

    Returns dict:
      'artikel'      : daftar artikel UNIK, terurut (terverifikasi dulu)
      'terverifikasi': jumlah DOI yang lolos audit CrossRef
      'sumber'       : jumlah per sumber (bukti failover bekerja)
      'kata_kunci'   : kata kunci yang dipakai (biar bisa diaudit manusia)
      'sumber_kata_kunci': 'kamus' | 'ai' | '' (dari mana kata kuncinya)
    """
    #  ⭐ 13Okt26 (putusan Bos 2A): KAMUS dulu; AI hanya kalau kamus gagal
    #     DAN pemanggil mengizinkan. Akar "hasil ngawur" = jatuh ke kata
    #     MENTAH saat konsep kosong ⇒ jalur itu DICABUT di sini.
    kw = kata_kunci(tema)
    #  ⚠️ 'kamus' HANYA kalau kamus BENAR-benar menemukan konsep. Kalau
    #     kosong, sumber = '' (jujur: belum dipetakan oleh siapa pun).
    sumber_kk = 'kamus' if kw.get('konsep') else ''
    #  ⚠️ 13Okt26 — jalur AI di sini memakai `kata_kunci_ai()` yang SINKRON
    #     (dengan `asyncio.run`). Karena itu jangan panggil dari event loop:
    #     dari RUTE pakai `pustaka.kata_kunci_ai_async()` + `cari_semua_dengan_konsep()`.
    if not kw.get('konsep') and pakai_ai:
        kw = kata_kunci_ai(tema)
        sumber_kk = 'ai' if kw.get('konsep') else ''
    return cari_semua_dengan_konsep(kw, tema, uji_tahun=uji_tahun,
                                    sumber_kk=sumber_kk)


def cari_semua_dengan_konsep(kw: dict, tema: str, uji_tahun: bool = True,
                             sumber_kk: str = '') -> dict:
    """Jalankan 4 MESIN NYATA memakai kata kunci yang SUDAH jadi.

    Dipisah (13Okt26) supaya RUTE async bisa memetakan kata kunci lewat
    `await` — tanpa memanggil `asyncio.run` di dalam event loop yang hidup.
    """
    if not kw.get('konsep'):
        log.info('[pustaka] tema=%r → TIDAK ada konsep (sumber=%r)',
                 tema, sumber_kk)
        return {'artikel': [], 'terverifikasi': 0, 'sumber': {},
                'kata_kunci': kw, 'sumber_kata_kunci': sumber_kk,
                'belum_dipetakan': True}

    log.info('[pustaka] tema=%r → en=%s id=%s (dari %s)',
             tema, kw['en'], kw['id'], sumber_kk)

    semua: list[dict] = []
    jumlah: dict[str, int] = {}
    #  ⭐ RUMUS PICO (26Sep26): AND antar konsep, OR di dalam konsep
    _garuda_kw = (kw.get('kw_garuda') or kw['id'])[:3]
    log.info('[pustaka] rumus Scopus   : %s', kw.get('q_scopus', '')[:200])
    log.info('[pustaka] rumus OpenAlex : %s', kw.get('q_openalex', ''))
    log.info('[pustaka] rumus CrossRef : %s', kw.get('q_crossref', ''))
    log.info('[pustaka] kata kunci Garuda: %s', _garuda_kw)
    for nama, hasil in (
        ('Scopus', cari_scopus(kw['en'], query_siap=kw.get('q_scopus', ''))),
        ('OpenAlex', cari_openalex(kw['en'], kw['id'],
                                   frasa=kw.get('q_openalex', ''))),
        ('Garuda', cari_garuda(_garuda_kw)),
        ('CrossRef', cari_crossref(kw['en'],
                                   frasa=kw.get('q_crossref', ''))),
    ):
        jumlah[nama] = len(hasil)
        semua.extend(hasil)

    #  Dedup (DOI dulu; kalau kosong pakai judul)
    unik: dict[str, dict] = {}
    for r in semua:
        k = _kunci_dedup(r)
        if not k:
            continue
        if k not in unik:
            unik[k] = r
        else:
            #  gabung: ambil abstrak kalau yang lama kosong
            if not unik[k].get('abstract') and r.get('abstract'):
                unik[k]['abstract'] = r['abstract']
    daftar = list(unik.values())

    #  Filter tahun (kecuali diminta tidak)
    if uji_tahun:
        daftar = [r for r in daftar
                  if not r.get('year')
                  or TAHUN_AWAL <= int(r['year']) <= TAHUN_AKHIR]

    #  ⭐ SARING: buang yang judulnya TIDAK menyentuh tema (temuan 26Sep26)
    sebelum = len(daftar)
    daftar = [r for r in daftar if _nyambung(r, kw)]
    log.info('[pustaka] saring nyambung: %s → %s artikel', sebelum, len(daftar))

    #  ⭐ AUDIT DOI — pagar anti-halusinasi (hanya untuk yang punya DOI)
    terverifikasi = 0
    for r in daftar:
        if r.get('doi'):
            r['doi_status'] = ('verified' if audit_doi(r['doi'])
                               else 'unverified')
            if r['doi_status'] == 'verified':
                terverifikasi += 1
        else:
            r['doi_status'] = 'no_doi'

    #  ⭐ MUTU JURNAL (12Okt26): tandai mutu tiap artikel ber-ISSN Scopus.
    #     Dijalankan PARALEL + cache 1 ISSN, supaya tidak menambah lama muat.
    for r in daftar:
        r['mutu'] = None
    _issns = sorted({(r.get('issn') or '').strip() for r in daftar
                     if (r.get('issn') or '').strip()})
    if _issns:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(6, len(_issns))) as _tp:
            _peta = dict(zip(_issns, _tp.map(mutu_jurnal, _issns)))
        for r in daftar:
            _k = (r.get('issn') or '').strip()
            if _k:
                r['mutu'] = _peta.get(_k)
        _ada = sum(1 for r in daftar if r.get('mutu'))
        log.info('[pustaka] mutu jurnal: %s/%s artikel bertanda', _ada, len(daftar))

    #  ⭐ INDIKATOR SCITE (12Okt26, PUTUSAN BOS): sitasi + jumlah pendukung &
    #     pembantah — GRATIS tanpa kunci. PARALEL + cache per DOI.
    #     ⚠️ None artinya "Scite tidak punya data" → layar JANGAN tampilkan
    #        apa-apa (bukan "0", bukan tulisan "Scite").
    for r in daftar:
        r['scite'] = None
    _dois = [((r.get('doi') or '').strip()) for r in daftar]
    _dois = [d for d in _dois if d]
    if _dois:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(8, len(_dois))) as _tp:
            _peta_s = dict(zip(_dois, _tp.map(scite_tallies, _dois)))
        for r in daftar:
            _d = (r.get('doi') or '').strip()
            if _d:
                r['scite'] = _peta_s.get(_d)
        _ada_s = sum(1 for r in daftar if r.get('scite'))
        log.info('[pustaka] scite: %s/%s artikel punya data', _ada_s, len(daftar))

    #  ⭐ DAFTAR ARTIKEL PENDUKUNG/PEMBANTAH (13Okt26, akun premium Bos lewat
    #     MCP Scite). Endpoint publik gratis HANYA angka; daftar + kutipan
    #     butuh token `EDUAI_SCITE_TOKEN`.
    #     ⚠️ PAGAR BIAYA/WAKTU: token kedaluwarsa 900 dtk & tiap panggilan
    #        mahal ⇒ HANYA untuk artikel yang SUDAH terbukti punya data,
    #        dan maksimal KUTIPAN_MAKS artikel per pencarian.
    #  ⭐ 13Okt26 (putusan Bos): 3 → 10 artikel.
    #  ALASAN: setelah perbaikan jalur banyak-DOI, kutipan untuk SEMUA
    #  artikel masuk dalam SATU panggilan ⇒ menambah artikel TIDAK
    #  menambah kuota (tetap 1). Manfaat: makin banyak indikator
    #  (didukung/dibantah + bagian) ⇒ user makin mudah memilih artikel.
    #  Biaya tambahan hanya waktu (~1-2 dtk) karena jawabannya lebih besar.
    KUTIPAN_MAKS = 10
    for r in daftar:
        r['kutipan'] = None
    _kandidat = [r for r in daftar
                 if r.get('scite') and (r.get('doi') or '').strip()]
    _kandidat.sort(key=lambda r: -(r.get('scite') or {}).get('dibantah') or 0)
    _kandidat = _kandidat[:KUTIPAN_MAKS]
    if _kandidat:
        #  ⭐ 13Okt26 — HEMAT KUOTA 90% (TERUKUR, putusan Bos).
        #  SEBELUM: ThreadPoolExecutor memanggil `scite_kutipan` PER DOI
        #  ⇒ 3 kandidat = 3 panggilan = 3 KUOTA Scite, padahal Scite
        #  menerima BANYAK DOI dalam SATU panggilan dan menghitung kuota
        #  PER PANGGILAN (diukur: 1 panggilan 1 kuota, 1 DOI atau 10 DOI
        #  sama saja). SEKARANG: kumpulkan semua DOI → SATU panggilan.
        #  🚨 JEBAKAN TERUKUR 13Okt26 (Wulan sendiri yang kena): DOI di
        #  daftar memakai awalan `https://doi.org/...`. Kalau pemetaan
        #  hasil memakai DOI KOTOR, padahal kunci `_peta_k` sudah
        #  DIBERSIHKAN di `scite_kutipan_banyak`, maka .get() SELALU
        #  gagal ⇒ kutipan hilang SENYAP padahal datanya ADA.
        #  Bukti: artikel "total 11 sitasi" tetap 0 kutipan; diuji
        #  langsung DOI-nya = 8 kutipan. ⇒ pakai `_doi_bersih()` di
        #  KEDUA sisi (kirim DAN baca).
        _dois = [_doi_bersih(r.get('doi')) for r in _kandidat]
        _peta_k = scite_kutipan_banyak(_dois, maks=5)
        for r in _kandidat:
            r['kutipan'] = _peta_k.get(_doi_bersih(r.get('doi')))
        _ada_k = sum(1 for r in daftar if r.get('kutipan'))
        log.info('[pustaka] scite kutipan: %s/%s artikel berdaftar '
                 '(1 panggilan untuk %s DOI)', _ada_k, len(_kandidat), len(_dois))

    #  Urutkan: terverifikasi dulu → jumlah sitasi terbanyak
    urut_status = {'verified': 0, 'no_doi': 1, 'unverified': 2}
    daftar.sort(key=lambda r: (urut_status.get(r.get('doi_status'), 3),
                               -(r.get('cited_by_count') or 0)))

    return {'artikel': daftar, 'terverifikasi': terverifikasi,
            'jumlah_per_sumber': jumlah, 'kata_kunci': kw,
            'total_unik': len(daftar),
            #  ⭐ 13Okt26: dari mana kata kuncinya ('kamus' | 'ai' | '')
            #     dipakai layar untuk memberi tahu user dengan jujur.
            'sumber_kata_kunci': sumber_kk,
            #  ⭐ (12Okt26, PUTUSAN BOS: "apikey wajib jelas, bukan diam-diam")
            #     Laporan apa adanya: mesin mana yang punya kunci & mana yang
            #     tidak. Dipakai layar untuk MEMBERI TAHU user, bukan menyembunyikan.
            'kunci': status_kunci()}


def status_kunci() -> dict:
    """Laporan TERBUKA: mesin mana yang punya kunci API, mana yang tidak.

    ⚠️ TIDAK pernah menampilkan nilai kunci — hanya ADA/TIDAK.
    Dipakai `cari_semua` (dilaporkan ke layar) dan halaman pemeriksa.
    """
    return {
        'Scopus': {'ada': bool(_kunci('scopus', 'EDUAI_SCOPUS_KEY')),
                   'perlu_kunci': True},
        'OpenAlex': {'ada': bool(_kunci('openalex', 'EDUAI_OPENALEX_KEY')),
                     'perlu_kunci': False},
        'Garuda': {'ada': True, 'perlu_kunci': False},
        'CrossRef': {'ada': True, 'perlu_kunci': False},
    }


def daftar_pustaka_apa7(artikel: list[dict]) -> str:
    """Susun daftar pustaka APA 7 dari artikel TERVERIFIKASI saja.

    Aturan (dari skill): HANYA referensi terverifikasi yang masuk daftar.
    """
    baris = []
    for r in artikel:
        if r.get('doi_status') not in ('verified', 'no_doi'):
            continue                       # unverified JANGAN masuk
        if not r.get('doi_status') == 'verified' and not r.get('garuda_id'):
            continue                       # tanpa DOI tapi ada GarudaID → boleh
        penulis = (r.get('authors') or '').strip()
        th = r.get('year') or 0
        judul = (r.get('title') or '').strip().rstrip('.')
        jurnal = (r.get('journal') or '').strip()
        doi = (r.get('doi') or '').strip()
        if not penulis or not th or not judul:
            continue
        teks = f'{penulis}. ({th}). {judul}.'
        if jurnal:
            teks += f' {jurnal}.'
        if doi:
            teks += f' {doi}'
        elif r.get('garuda_id'):
            teks += (' https://garuda.kemdiktisaintek.go.id/documents/detail/'
                     f'{r["garuda_id"]}')
        baris.append(teks)
    baris.sort()
    return '\n\n'.join(baris)


def ringkas_untuk_ai(tema: str, maks: int = 20) -> str:
    """Bentuk teks SIAP PAKAI untuk prompt AI (kerangka per bab).

    Bentuk: nomor. Penulis (Tahun). Judul. Jurnal. DOI — status.
    Dipakai supaya AI HANYA boleh mengutip dari daftar ini.
    """
    h = cari_semua(tema)
    baris = [f'# REFERENSI TERVERIFIKASI — tema: {tema}',
             f'(terverifikasi CrossRef: {h["terverifikasi"]} dari '
             f'{h["total_unik"]} artikel unik)',
             '# ATURAN: HANYA kutip dari daftar ini. Dilarang mengarang.',
             '']
    for i, r in enumerate(h['artikel'][:maks], 1):
        st = {'verified': '✅ terverifikasi',
              'no_doi': '⚪ tanpa DOI',
              'unverified': '⚠️ DOI tidak lolos'}.get(r.get('doi_status'), '?')
        baris.append(f'{i}. {r.get("authors") or "-"} ({r.get("year") or "-"}). '
                     f'{r.get("title") or "-"}. '
                     f'{r.get("journal") or "-"}. '
                     f'{r.get("doi") or "tanpa DOI"} — {st}')
    return '\n'.join(baris)


def link_garuda(garuda_id) -> str:
    """Tautan halaman artikel di Garuda (dipakai tampilan & daftar pustaka)."""
    if not garuda_id:
        return ''
    return (f'https://garuda.kemdiktisaintek.go.id/documents/detail/{garuda_id}')


def pdf_terbuka(url: str) -> dict:
    """Ambil PDF kalau artikelnya OPEN ACCESS (TIDAK menembus paywall).

    Kembalikan {'ok': True, 'isi', 'ukuran', 'url'} atau {'ok': False, 'sebab'}.
    ATURAN BOS 06Okt26: 'jangan download artikel, kasih daftar LINK
    (lebih jujur)' ⇒ yang berbayar cukup dapat LINK, bukan dipaksa unduh.
    """
    if not url:
        return {'ok': False, 'sebab': 'tanpa tautan'}
    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = httpx.get(url, headers=hdr, timeout=60, follow_redirects=True)
    except Exception as e:                                    # noqa: BLE001
        return {'ok': False, 'sebab': f'gagal menghubungi: {type(e).__name__}'}
    if r.status_code != 200:
        return {'ok': False, 'sebab': f'balasan {r.status_code}'}
    isi = r.content or b''
    if isi[:4] != b'%PDF':
        return {'ok': False, 'sebab': 'bukan PDF (kemungkinan berbayar)'}
    return {'ok': True, 'isi': isi, 'ukuran': len(isi), 'url': url}


def unduh_pdf(artikel: dict, url_pdf: str = '') -> dict:
    """Siapkan unduhan PDF untuk SATU artikel (dipakai rute `/jurnal/unduh`).

    Sumber URL: `url_pdf` kiriman pemanggil, atau `pdf_url` di data artikel.
    Kalau tidak ada/berbayar → {'ok': False, 'sebab'} (pemanggil beri LINK).
    """
    if not isinstance(artikel, dict):
        return {'ok': False, 'sebab': 'data artikel tidak sah'}
    url = (url_pdf or artikel.get('pdf_url') or artikel.get('url_pdf') or '')
    if not url:
        return {'ok': False, 'sebab': 'artikel tidak menyertakan tautan PDF'}
    return pdf_terbuka(url)


def sehat() -> dict:
    """Periksa kesehatan: kunci ada? sumber bisa dihubungi? (untuk /health)."""
    hasil = {'scopus_key': bool(_kunci('scopus', 'EDUAI_SCOPUS_KEY')),
             'openalex_key': bool(_kunci('openalex', 'EDUAI_OPENALEX_KEY')),
             'sumber': {}}
    for nama, fn in (('Scopus', lambda: cari_scopus(['cricket'], 1)),
                     ('OpenAlex', lambda: cari_openalex(['cricket'], None, 1)),
                     ('Garuda', lambda: cari_garuda(['pendidikan'], 1)),
                     ('CrossRef', lambda: cari_crossref(['cricket'], 1))):
        try:
            hasil['sumber'][nama] = len(fn()) > 0
        except Exception:                                     # noqa: BLE001
            hasil['sumber'][nama] = False
    return hasil


if __name__ == '__main__':          # uji manual: python -m app.pustaka "tema"
    import sys
    logging.basicConfig(level=logging.INFO)
    t = sys.argv[1] if len(sys.argv) > 1 else 'aktivitas fisik dan siklus menstruasi'
    print(ringkas_untuk_ai(t))
