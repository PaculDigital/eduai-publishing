"""Modernisasi skenario P — ganti blok P lama (asumsi 1 koneksi) dengan
desain BARU: simpan semua → matikan semua → probe bukti → uji → restore persis.

Akar (28Sep26, ACC Bos): 9router kini multi-aktif + strategy=fallback →
mematikan CB saja TIDAK memutus jalur (TH1 menyelamatkan) → P3/P4/P5 gagal.

Backup dulu: _arsip/pre-modernisasi-p-20260928/ + MD5.
"""
import hashlib
import os
import shutil
import sys

BERKAS = '_uji_publik_komentar.py'
CADANGAN_DIR = '_arsip/pre-modernisasi-p-20260928'

# ── 1. BACKUP ──────────────────────────────────────────────────────────
os.makedirs(CADANGAN_DIR, exist_ok=True)
shutil.copy2(BERKAS, os.path.join(CADANGAN_DIR, BERKAS))
with open(BERKAS, 'rb') as fh:
    md5_lama = hashlib.md5(fh.read()).hexdigest()
with open(os.path.join(CADANGAN_DIR, 'MD5.txt'), 'w') as fh:
    fh.write(f'{md5_lama}  {BERKAS}  (pra-modernisasi-p 28Sep26)\n')
print(f'backup: {CADANGAN_DIR}/{BERKAS} md5={md5_lama[:12]}')

# ── 2. HELPER BARU (disisipkan sebelum PEMISAH UJI BERAT) ─────────────
HELPER = r'''def _9r(kode: str) -> tuple[int, str]:
    """Jalankan potongan NODE terhadap DB 9router (lewat `docker exec`).

    Kode di-BASE64 dulu → aman dari kutipan shell (`eval(Buffer...)`).
    """
    import base64
    b64 = base64.b64encode(kode.encode()).decode()
    isi = "eval(Buffer.from('" + b64 + "','base64').toString())"
    return _docker('docker exec 9router node -e "' + isi + '"')


def _id_aktif_9r() -> list:
    """Daftar id koneksi 9router dengan `isActive=1` (urut, tanpa sortir)."""
    rc, out = _9r("console.log('AKTIF=' + JSON.stringify("
                  "s.prepare('SELECT id FROM providerConnections "
                  "WHERE isActive=1 ORDER BY id').all().map(r=>r.id)))")
    for baris in out.splitlines():
        if baris.startswith('AKTIF='):
            try:
                return json.loads(baris.split('=', 1)[1])
            except (ValueError, TypeError):
                return []
    return []


def _set_aktif_9r(ids: list, nilai: int) -> int:
    """Set `isActive=<nilai>` untuk persis id-id `ids`. Balas JUMLAH baris kena."""
    if not ids:
        return 0
    daftar = ','.join("'" + str(i).replace("'", '') + "'" for i in ids)
    kode = ('const st=s.prepare("UPDATE providerConnections SET isActive='
            + str(int(nilai)) + ' WHERE id IN (' + daftar + ')");'
            "st.run();console.log('KENA=' + st.changes)")
    rc, out = _9r(kode)
    for baris in out.splitlines():
        if baris.startswith('KENA='):
            try:
                return int(baris.split('=', 1)[1])
            except ValueError:
                return 0
    return 0


def _probe_9router(max_tok: int = 16) -> str:
    """Probe LANGSUNG combo `EduAi` ke 9router — BUKTI nyata, bukan asumsi.

    'hidup' = masih bisa melayani (ada `choices`) · 'mati' = tak bisa
    melayani (tak terjangkau / error tanpa `choices`).
    Kalibrasi WAJIB: probe dipercaya HANYA kalau SEBELUM dimatikan dia
    bilang 'hidup' (bukti alat ukur ini bisa melihat hidup & mati).
    """
    key = ''
    try:
        with open('.env') as fh:
            for baris in fh:
                if baris.startswith('EDUAI_ROUTER_KEY='):
                    key = baris.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    except OSError:
        pass
    isi = json.dumps({'model': 'EduAi',
                      'messages': [{'role': 'user', 'content': 'Balas: OK'}],
                      'max_tokens': max_tok, 'temperature': 0.2}).encode()
    req = urllib.request.Request(
        'http://127.0.0.1:20128/v1/chat/completions', data=isi,
        headers={'Authorization': 'Bearer ' + key,
                 'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            j = json.loads(r.read().decode('utf-8', 'ignore') or '{}')
        return 'hidup' if j.get('choices') else 'mati'
    except urllib.error.HTTPError:
        return 'mati'           # server menjawab TANPA `choices` = tak layan
    except (urllib.error.URLError, OSError):
        return 'mati'           # tak terjangkau = tak bisa melayani


'''

# ── 3. BLOK P BARU ─────────────────────────────────────────────────────
BLOK_P = r'''        jeda('sebelum P (gangguan provider)')

        # ── P. GANGGUAN PROVIDER AI (jalur 1 benar-benar diputus) ───────
        #  DESAIN BARU (28Sep26, ACC Bos) — akar GAGAL P3/P4/P5 putaran
        #  28Sep siang: 9router kini punya BEBERAPA koneksi aktif (combo
        #  strategy=fallback) → mematikan koneksi CB saja TIDAK memutus
        #  jalur: cadangan TH1 tetap melayani → job `selesai` → P3/P4/P5
        #  gagal demi asumsi basi "tepat 1 koneksi".
        #  Kini: simpan SEMUA id aktif → matikan SEMUA → PROBE 9router
        #  (dua langkah: 'hidup' SEBELUM + 'mati' SESUDAH = alat ukur
        #  terkalibrasi) → uji perilaku app → restore PERSIS daftar semula
        #  di `finally` (produksi tidak pernah tertinggal mati walau uji
        #  crash). Koneksi 9router = milik Bos (ACC 28Sep: sengaja aktif,
        #  biarkan) — uji hanya mematikan SEMENTARA lalu mengembalikan.
        #  ⚠️ Sejak 17Sep26: JANGAN `WHERE isActive=0` (pernah menghidupkan
        #  SEMUA 25 koneksi); SELALU by id simpanan.
        kuota_reset_berat(5)   # WAJIB: P dulu gagal karena kena 402 kuota habis

        probe_awal = _probe_9router()
        info(f'probe 9router SEBELUM dimatikan: {probe_awal}')
        id_awal = _id_aktif_9r()
        cek('P0 koneksi aktif tercatat sebagai dasar restore',
            bool(id_awal),
            f'{len(id_awal)} aktif: ' + ','.join(x[:8] for x in id_awal))
        stP, ringP = ('', {})
        try:
            kena = _set_aktif_9r(id_awal, 0)
            sisa_aktif = _id_aktif_9r()
            probe_sesudah = (_probe_9router()
                             if probe_awal == 'hidup' else 'ragu')
            #  `kuat` = alat ukur terkalibrasi DAN benar-benar mati;
            #  kalau probe tak pernah terbukti 'hidup', P1 TETAP jujur:
            #  berdiri pada hitungan DB + catat probe apa adanya.
            kuat = (probe_awal != 'hidup') or (probe_sesudah == 'mati')
            cek('P1 SEMUA koneksi dimatikan + 9router terbukti tak layan',
                kena == len(id_awal) and not sisa_aktif and kuat,
                f'kena={kena}/{len(id_awal)} · sisa_aktif={len(sisa_aktif)}'
                f' · probe {probe_awal}→{probe_sesudah}'
                + ('' if probe_awal == 'hidup'
                   else ' (probe tak terkalibrasi — P1 berdiri di hitungan DB)'))
            s, b, _ = buka('/api/ai/v1/revisi',
                           data={'naskah': 'BAB I PENDAHULUAN\n\nIsi uji.',
                                 'komentar': ['Perbaiki.']},
                           metode='POST', timeout=60)
            kodeP = ''
            try:
                kodeP = (json.loads(b) or {}).get('kode') or ''
            except Exception:                                  # noqa: BLE001
                pass
            cek('P2 permintaan TETAP diterima walau jalur 1 putus (tidak 500)',
                s in (200, 409), f'HTTP {s} · {b[:110]}')
            if kodeP:
                #  900 dtk > AI_TIMEOUT (420) + jalur 2 → "menggantung" =
                #  tidak pernah capai status akhir sampai batas sabar.
                stP, ringP = tunggu_proses(kodeP, batas_detik=900)
                #  P3 (baru): WAJIB sampai status AKHIR — boleh `selesai`
                #  (jalur 2 menyelamatkan = fitur) ATAU `gagal` (jujur);
                #  TIDAK boleh menggantung di `jalan`/timeout.
                cek('P3 sampai status akhir (tidak menggantung)',
                    stP in ('selesai', 'gagal'), f'status={stP or "(kosong)"}')
                #  P4 (baru): kalau gagal → alasan wajib terbaca user;
                #  kalau selesai → catat model pelengkap (bukti jalur 2).
                galatP = str(ringP.get('galat') or '')
                mdlP = str(ringP.get('model_ai') or ringP.get('model') or '-')
                cek('P4 gagal → galat terbaca; selesai → model tercatat',
                    (stP != 'gagal') or bool(galatP.strip()),
                    f'status={stP} · model={mdlP} · galat={galatP[:90]}')
                info(f'KODE_PROSES_P={kodeP}')
        finally:
            #  RESTORE PERSIS id yang sama — bukan 'aktifkan 1' (basi),
            #  bukan `WHERE isActive=0` (bug 17Sep26).
            if id_awal:
                _set_aktif_9r(id_awal, 1)
        setelah = set(_id_aktif_9r())
        hilang = ','.join(x[:8] for x in (set(id_awal) - setelah))
        cek('P5 restore PERSIS seperti semula (id & jumlah sama)',
            bool(id_awal) and setelah == set(id_awal),
            f'awal={len(id_awal)} → sesudah={len(setelah)} · hilang={hilang or "-"}')
        jeda('sebelum Q (naskah raksasa)')'''

# ── 4. GANTI ───────────────────────────────────────────────────────────
with open(BERKAS) as fh:
    t = fh.read()

m_pemb = '#  PEMISAH UJI BERAT (17Sep26)'
m_mulai = "        jeda('sebelum P (gangguan provider)')"
m_akhir = "        jeda('sebelum Q (naskah raksasa)')"
for nama, m in (('PEMISAH', m_pemb), ('mulai-P', m_mulai), ('akhir-P', m_akhir)):
    if t.count(m) != 1:
        print(f'GAGAL: penanda {nama} ditemukan {t.count(m)}× (harus 1)')
        sys.exit(1)

# sisipkan helper sebelum SELURUH banner PEMISAH (cari baris ═ di atasnya)
i_pemb = t.index(m_pemb)
awal_baris = t.rfind('\n# ═', 0, i_pemb) + 1
t = t[:awal_baris] + HELPER + t[awal_baris:]
a = t.index(m_mulai)
b = t.index(m_akhir)
t = t[:a] + BLOK_P + t[b:]

with open(BERKAS, 'w') as fh:
    fh.write(t)
print('blok P diganti; helper _9r/_id_aktif_9r/_set_aktif_9r/_probe_9router disisipkan')

# ── 5. VERIFIKASI DASAR ────────────────────────────────────────────────
import ast
ast.parse(t)
sisa = [k for k in ('sql_mati', 'ID_PROVIDER', '_P_BISA', 'WHERE isActive=0')
        if k in t]
print('sisa penanda lama:', sisa if sisa else 'TIDAK ADA ✅')
print('kompilasi AST OK ✅')
