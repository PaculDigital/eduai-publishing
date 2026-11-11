"""Gerbang 3-naskah — pemeriksaan otomatis sebelum pilot produksi Jev 1.14.

ATURAN GERBANG (ditulis di sini, bukan dikarang diam-diam):
  G1  BAB HILANG: FAIL bila ada judul BAB baseline yang tidak ada di
      peta baru. Baseline = gabungan judul BAB dari 3 run live v7
      (gerbang_baseline.json). Karena satu run Jev bisa menjatuhkan satu
      BAB karena variansi (terukur v7: fid=112 run 1 kehilangan BAB III,
      fid=115 run 3 kehilangan BAB II), satu run yang kehilangan = derau,
      bukan regresi (dicatat sebagai peringatan). FAIL bila BAB itu hilang
      di >= 2 run (gerbang jalan 2 run; bila 1 run saja, hilang di run itu
      = FAIL).
  G2  SUBBAB BERUBAH: FAIL bila median subbab peta baru menyimpang lebih
      dari AMBANG per naskah dari median baseline. Ambang per naskah
      (tersimpan di gerbang_baseline.json, field 'ambang_g2') dihitung
      dari sebaran antar-run yang terukur, BUKAN satu angka global:
        ambang_g2 = ceil((max(subbab_run) - min(subbab_run)) / 2) + 2
      dengan subbab_run = semua run v9/v10 yang tersimpan. Nilai saat ini
      (baseline v10, 11 Nov 2026, 4 run): 81=3 (4 run, 129-130, median
      130.0), 112=8 (4 run, 76-88, median 82.5), 115=6 (4 run, 79-87,
      median 82.0). "+2" adalah margin eksplisit untuk sesi yang belum
      teramati (n kecil, rentang sejati lebih lebar) — lebih kecil dari
      regresi terkecil yang gerbang wajib tangkap (+10 subbab, kasus
      uji mandiri 5). Konsekuensi jujur: gerbang TIDAK bisa membedakan
      regresi kecil dari drift model biasa; ia hanya menangkap regresi
      besar. PERHATIAN: ambang 112 kini 8 (dulu 4 pada baseline 2-run)
      karena sesi2 segar memberi 76 dan 88 — median 4 run tetap 82.5,
      yang melebar hanya sebaran. Baseline v9 2-run tersimpan di
      ground_truth/gerbang_baseline_v9_2run.json; baseline 1.14 (v8)
      di gerbang_baseline_114.json. Keduanya TIDAK berlaku lagi untuk
      menilai run v10: gerbang v9 GAGAL melawan baseline v8 (112 median
      84 vs 80.0, 115 median 87 vs 75.5) karena pergeseran SISTEMATIS
      aturan R2-1/R2-2 (judul bernomor 1 tingkat dipertahankan sebagai
      subbab, butir dash dipisah) — bukan regresi (skor-teks tidak
      turun, goyang antar-run turun). Median diambil dari 2 run (bila
      2 run) atau 1 run (cara gerbang: sorted[len//2], upper-middle).
  BATAS DETEKSI (v10, 11 Nov 2026, jangan disembunyikan): ambang G2=3
  (81), 8 (112), 6 (115). Regresi yang menggeser median sesi melebihi
  ambang itu tertangkap; regresi di bawah ambang TIDAK bisa dibedakan
  dari drift model — untuk 112, gerbang kini hanya menangkap regresi
  >8 subbab, itu harga drift 1.14 yang terukur (rentang 12 antar 4
  run). Sesi v10 berikutnya bisa duduk di batas ambang padahal bukan
  regresi. Jadi G2 yang gagal mepet (selisih 4-5) harus diulang satu
  sesi segar sebelum divonis regresi.
  G1  CATATAN PENGUKURAN (10 Nov 2026): daftar 'bab' pelari live
      (jalankan_gerbang.py) adalah GABUNGAN label Jev + judul gabung
      kode, sedangkan daftar 'bab' baseline hanya label Jev. Karena itu
      baseline BAB tetap gabungan label Jev v7 (112/115: II-V; 81: I-V
      dari gabung kode yang terbukti selaras) — diwarisi baseline 1.13,
      struktur naskah tidak berubah dengan model — dan TIDAK ditambah
      BAB I / BAB VI dari daftar gabung gerbang — judul BAB VI yang sama
      persis di dua naskah berbeda menunjukkan ia berasal dari jalur
      gabung, bukan pengukuran Jev. Soal BAB VI sudah masuk paket
      sengketa (ground_truth_115.tsv baris 69) menunggu label manusia.
  G3  JUDUL BAB SAMPAH: FAIL bila ada judul BAB di peta baru yang:
      - panjangnya > 80 karakter, ATAU
      - mengandung '. ' (tanda kalimat di tengah judul), ATAU
      - tidak diawali 'BAB' (setelah kupas nomor 'N. '), ATAU
      - mengandung 'bagian ini menjelaskan' (pola sampah WULAN-1 run 2).
      Aturan ini menangkap kalimat utuh yang dilabel BAB, bukan judul.

CARA PAKAI:
  python3 gerbang_3_naskah.py --uji
      Uji mandiri offline (tanpa Jev): peta v7 asli harus LOLOS, peta
      mutasi (BAB dibuang, subbab +10, judul sampah) harus GAGAL.
  python3 gerbang_3_naskah.py --mode offline --peta MAPS.json
      Nilai peta tersimpan. MAPS.json: {"81": [run1, run2], "112": [...],
      "115": [...]}; tiap run: {"bab": [...], "subbab_jml": int}.
      Boleh 1 run per naskah (aturan G1 jadi: hilang di run itu = FAIL).
  python3 gerbang_3_naskah.py --mode live --ya-saya-tahu-biaya
      Jalankan pemetaan live 2 run x 3 naskah di container (lewat
      jalankan_gerbang.py), lalu nilai. BIAYA: ~170 panggilan Jev
      (2 x (41 + 37 + 7), dari angka live 1.14) dan ~2 menit wall.
      Tanpa flag --ya-saya-tahu-biaya, hanya mencetak biaya + perintah.

Keluar: exit 0 bila gerbang LOLOS, exit 1 bila GAGAL (pesan pelanggaran
dicetak). Tidak push, tidak merge, tidak deploy.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE_PATH = ROOT / 'ground_truth' / 'gerbang_baseline.json'

AMBANG_SUBBAB_SELISIH = 5  # fallback bila baseline belum punya ambang_g2
PANJANG_JUDUL_SAMPAH = 80

# Biaya live (dari angka live 1.14, 10 Nov 2026) — ditulis, bukan dikarang.
BIAYA_LIVE_PER_RUN = {'112': 41, '115': 37, '81': 7}
RUN_LIVE_PER_NASKAH = 2


def normal_bab(judul):
    return re.sub(r'^\d+\.\s*', '', (judul or '').strip())


def judul_sampah(judul):
    """True bila judul BAB ini sampah (kalimat, bukan judul)."""
    t = normal_bab(judul)
    if len(t) > PANJANG_JUDUL_SAMPAH:
        return 'panjang %d kar > %d' % (len(t), PANJANG_JUDUL_SAMPAH)
    if '. ' in t:
        return 'mengandung kalimat (. di tengah judul)'
    if not re.match(r'^BAB\s+[IVX0-9]+', t):
        return 'tidak diawali penanda BAB'
    if 'bagian ini menjelaskan' in t.lower():
        return 'pola sampah WULAN-1 (kalimat penjelasan)'
    return None


def nilai_run(peta_run, baseline_naskah):
    """Nilai SATU run. Kembalikan daftar pelanggaran (kosong = lolos)."""
    pel = []
    bab_baru = [normal_bab(b) for b in (peta_run.get('bab') or [])]
    for b in baseline_naskah['bab']:
        if b not in bab_baru:
            pel.append('G1 BAB hilang: %s' % b)
    for b in bab_baru:
        sebab = judul_sampah(b)
        if sebab:
            pel.append('G3 judul BAB sampah: %r (%s)' % (b[:80], sebab))
    return pel


def nilai_naskah(runs, baseline_naskah, fid):
    """Nilai SATU naskah dari 1-3 run. G1: FAIL bila satu judul BAB hilang
    di >= 2 run (atau di satu-satunya run bila hanya 1 run); hilang di
    1 run dari >= 2 run = derau (peringatan). G3 langsung gagal."""
    if not runs:
        return False, ['tidak ada run untuk fid=%s' % fid], []
    peringatan = []
    # G3 dulu (judul sampah di run mana pun = gagal langsung)
    for r in runs:
        for p in nilai_run(r, baseline_naskah):
            if not p.startswith('G1'):
                return False, [p], peringatan
    # G1: hitung di berapa run tiap judul BAB hilang
    hilang_hitung = {}
    for r in runs:
        for p in nilai_run(r, baseline_naskah):
            if p.startswith('G1'):
                hilang_hitung[p] = hilang_hitung.get(p, 0) + 1
    ambang_gagal = 1 if len(runs) == 1 else 2
    gagal = sorted(p for p, c in hilang_hitung.items() if c >= ambang_gagal)
    if gagal:
        return False, gagal, peringatan
    for p in sorted(hilang_hitung):
        peringatan.append('derau (bukan gagal): %s' % p)
    # G2: subbab vs median baseline, ambang per naskah dari baseline
    subbab = [r.get('subbab_jml') for r in runs if r.get('subbab_jml') is not None]
    if subbab:
        med = sorted(subbab)[len(subbab) // 2]
        ambang = baseline_naskah.get('ambang_g2', AMBANG_SUBBAB_SELISIH)
        if abs(med - baseline_naskah['subbab_median']) > ambang:
            return False, ['G2 subbab berubah: median run %s vs baseline %s '
                           '(selisih %s > ambang fid=%s %s)'
                           % (med, baseline_naskah['subbab_median'],
                              abs(med - baseline_naskah['subbab_median']),
                              fid, ambang)], peringatan
    return True, [], peringatan


def nilai_gerbang(maps_by_fid, baseline):
    """maps_by_fid: {'81': [run, ...], '112': [...], '115': [...]}."""
    lolos_semua = True
    hasil = {}
    for fid in ('81', '112', '115'):
        ok, pel, per = nilai_naskah(maps_by_fid.get(fid) or [],
                                    baseline[fid], fid)
        hasil[fid] = {'lolos': ok, 'pelanggaran': pel, 'peringatan': per}
        lolos_semua = lolos_semua and ok
    return lolos_semua, hasil


def muat_baseline():
    return json.load(open(BASELINE_PATH, encoding='utf-8'))


def muat_peta_v7():
    """Peta tersimpan v7 (hasil_v7_live.json) sebagai peta 'baik'.

    Perhatian fid=81: daftar 'bab' JSON v7 kosong — judul BAB di sana
    diputuskan kode (gabung), bukan label Jev. Judul BAB 81 di sini
    diambil dari gabung kode rekonstruksi lokal, yang TERBUKTI selaras
    persis dengan live (kand 486, buang 720, gabung 10, mock Jev 0).
    Runner live (jalankan_gerbang.py) mengeluarkan gabungan yang sama
    dari run-nya sendiri, jadi ini bukan lingkaran tertutup."""
    v7 = json.load(open(ROOT / 'hasil_v7_live.json', encoding='utf-8'))
    baseline = muat_baseline()
    out = {}
    for fid in ('81', '112', '115'):
        runs = []
        for r in v7[fid]:
            bab = list(r.get('bab') or [])
            if fid == '81' and not bab:
                bab = list(baseline['81']['bab'])
            runs.append({'bab': bab,
                         'subbab_jml': r.get('label', {}).get('subbab', 0)})
        out[fid] = runs
    return out


def muat_peta_114():
    """Peta tersimpan 1.14 (hasil_baseline114.json) sebagai peta 'baik'.

    2 run per naskah; 'bab' = daftar gabung pelari live (Jev + gabung
    kode), sama seperti yang dikeluarkan jalankan_gerbang.py. Dipakai
    uji mandiri sejak baseline pindah ke 1.14 (10 Nov 2026): peta v7
    (1.13) tidak lagi lolos G2 melawan baseline 1.14 (112 selisih 4,
    115 selisih 6.5 dari median baru), jadi peta 'baik' harus dari
    model yang sama dengan baseline.
    """
    d = json.load(open(ROOT / 'hasil_baseline114.json', encoding='utf-8'))
    out = {}
    for fid in ('81', '112', '115'):
        out[fid] = [{'bab': list(r.get('bab') or []),
                     'subbab_jml': r.get('subbab_jml')}
                    for r in d['run'][fid]]
    return out


def muat_peta_r2():
    """Peta tersimpan v9 (hasil_r2_114.json) sebagai peta 'baik'.

    2 run per naskah; 'bab' = daftar gabung pelari live (Jev + gabung
    kode), sama seperti yang dikeluarkan jalankan_gerbang.py. Dipakai
    uji mandiri sejak baseline pindah ke v9 (11 Nov 2026): peta 1.14
    (v8) tidak lagi lolos G2 melawan baseline v9 (112 selisih 2,5,
    115 selisih 7,5 dari median baru — pergeseran sistematis aturan
    R2-1/R2-2, bukan regresi), jadi peta 'baik' harus dari aturan
    yang sama dengan baseline.
    """
    d = json.load(open(ROOT / 'hasil_r2_114.json', encoding='utf-8'))
    out = {}
    for fid in ('81', '112', '115'):
        out[fid] = [{'bab': list(r.get('bab') or []),
                     'subbab_jml': r['label_hitung'].get('subbab')}
                    for r in d['run'][fid]]
    return out


def uji_mandiri():
    """Uji offline: 6 kasus. Semua harus berperilaku sesuai harapan."""
    baseline = muat_baseline()
    p114 = muat_peta_r2()
    kasus = []

    def tambah(nama, maps, harap_lolos):
        ok, hasil = nilai_gerbang(maps, baseline)
        kasus.append((nama, harap_lolos, ok, hasil))

    # 1. peta v9 asli (2 run) -> harus LOLOS
    tambah('v9 asli (2 run)', {k: v[:2] for k, v in p114.items()}, True)
    # 2. peta v9 asli (1 run saja) -> harus LOLOS (jalur 1 run)
    tambah('v9 asli (1 run)', {k: v[:1] for k, v in p114.items()}, True)
    # 3. BAB dibuang di KEDUA run fid=112 -> harus GAGAL (G1)
    m = json.loads(json.dumps(p114))
    for r in m['112'][:2]:
        r['bab'] = [b for b in r['bab'] if 'BAB III' not in b]
    tambah('BAB III hilang di 2 run (112)', m, False)
    # 4. BAB dibuang di SATU run saja -> harus LOLOS (derau) + peringatan
    m = json.loads(json.dumps(p114))
    m['112'][0]['bab'] = [b for b in m['112'][0]['bab'] if 'BAB III' not in b]
    tambah('BAB III hilang di 1 run saja (derau)', m, True)
    # 5. subbab +10 di fid=81 -> harus GAGAL (G2)
    m = json.loads(json.dumps(p114))
    for r in m['81']:
        r['subbab_jml'] = r['subbab_jml'] + 10
    tambah('subbab +10 (81)', m, False)
    # 6. judul BAB sampah di fid=115 -> harus GAGAL (G3)
    m = json.loads(json.dumps(p114))
    m['115'][0]['bab'] = list(m['115'][0]['bab']) + [
        'bagian ini menjelaskan tentang jenis, waktu, dan tempat desain.']
    tambah('judul BAB sampah (115)', m, False)

    semua_ok = True
    for nama, harap, dapat, hasil in kasus:
        cocok = (harap == dapat)
        semua_ok = semua_ok and cocok
        print('  [%s] %s (harap %s, dapat %s)'
              % ('LULUS' if cocok else 'GAGAL-UJI',
                 nama, 'LOLOS' if harap else 'GAGAL',
                 'LOLOS' if dapat else 'GAGAL'))
        if not cocok:
            print('      hasil:', json.dumps(hasil, ensure_ascii=False))
    print('HASIL UJI MANDIRI: %d/%d kasus berperilaku benar'
          % (sum(1 for _, h, d, _ in kasus if h == d), len(kasus)))
    return semua_ok


def biaya_live():
    total = RUN_LIVE_PER_NASKAH * sum(BIAYA_LIVE_PER_RUN.values())
    return total


def jalankan_live():
    """Orkestrasi live: kirim kode + runner ke container, jalankan,
    ambil JSON, nilai. Dijalankan hanya dengan --ya-saya-tahu-biaya."""
    import tarfile, io
    print('Biaya live: ~%d panggilan Jev (2 run x 3 naskah), ~2 menit.'
          % biaya_live())
    print('Menyiapkan scratch di container eduai-app ...')
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as tar:
        for nama in ('peta3_jev.py', 'jalankan_gerbang.py'):
            tar.add(ROOT / nama, arcname=nama)
        tar.add(ROOT / 'app', arcname='app')
        tar.add(ROOT / 'profil', arcname='profil')
        # 10 Nov 2026: app/ai.py:363 membaca prompts/revisi_produksi.txt
        # lewat Path(__file__).parent.parent/'prompts' — dari scratch itu
        # /tmp/jev-gerbang/prompts. Tanpa ini run gagal di start (0 Jev
        # terbuang), sama seperti uji v7 yang butuh tambahan prompts/.
        tar.add(ROOT / 'prompts', arcname='prompts')
    open('/tmp/jev-gerbang.tar', 'wb').write(buf.getvalue())
    cmds = (
        'docker exec eduai-app mkdir -p /tmp/jev-gerbang && '
        'docker cp /tmp/jev-gerbang.tar eduai-app:/tmp/jev-gerbang.tar && '
        'docker exec eduai-app tar xf /tmp/jev-gerbang.tar -C /tmp/jev-gerbang && '
        'docker exec eduai-app python3 /tmp/jev-gerbang/jalankan_gerbang.py'
    )
    print('Perintah live (dijalankan lewat SSH ke server Boss):')
    print(' ', cmds)
    ssh = ['ssh', '-p', '22', '-o', 'StrictHostKeyChecking=accept-new',
           '-o', 'ProxyCommand=python3 /home/hatch/.ssh/tsconnect.py %h %p',
           '-o', 'IdentitiesOnly=yes', '-i', '/home/hatch/.ssh/id_ed25519',
           '-o', 'UserKnownHostsFile=/home/hatch/.ssh/known_hosts',
           'ubuntu@100.78.203.64', cmds]
    # tar harus ada di server dulu: kirim lewat scp
    scp = ['scp', '-P', '22', '-o', 'StrictHostKeyChecking=accept-new',
           '-o', 'ProxyCommand=python3 /home/hatch/.ssh/tsconnect.py %h %p',
           '-o', 'IdentitiesOnly=yes', '-i', '/home/hatch/.ssh/id_ed25519',
           '-o', 'UserKnownHostsFile=/home/hatch/.ssh/known_hosts',
           '/tmp/jev-gerbang.tar', 'ubuntu@100.78.203.64:/tmp/jev-gerbang.tar']
    r = subprocess.run(scp, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print('GAGAL kirim tar:', r.stderr[-500:])
        return 1
    r = subprocess.run(ssh, capture_output=True, text=True, timeout=900)
    print(r.stdout[-4000:])
    if r.returncode != 0:
        print('GAGAL jalan live:', r.stderr[-500:])
        return 1
    try:
        # 10 Nov 2026: pelari mencetak 'SELESAI' sesudah baris GERBANG_MAPS,
        # jadi json.loads() pada sisa stdout gagal 'Extra data'. Pakai
        # raw_decode supaya hanya objek JSON pertama yang dibaca.
        teks = r.stdout[r.stdout.rindex('{"81"'):]
        maps, _ = json.JSONDecoder().raw_decode(teks)
    except Exception as e:
        print('GAGAL baca JSON live:', e)
        return 1
    ok, hasil = nilai_gerbang(maps, muat_baseline())
    print(json.dumps(hasil, ensure_ascii=False, indent=2))
    print('GERBANG:', 'LOLOS' if ok else 'GAGAL')
    return 0 if ok else 1


def main(argv):
    if '--uji' in argv:
        return 0 if uji_mandiri() else 1
    if '--mode' in argv and argv[argv.index('--mode') + 1] == 'offline':
        jalan = argv[argv.index('--peta') + 1]
        maps = json.load(open(jalan, encoding='utf-8'))
        ok, hasil = nilai_gerbang(maps, muat_baseline())
        print(json.dumps(hasil, ensure_ascii=False, indent=2))
        print('GERBANG:', 'LOLOS' if ok else 'GAGAL')
        return 0 if ok else 1
    if '--mode' in argv and argv[argv.index('--mode') + 1] == 'live':
        print('Biaya live gerbang: ~%d panggilan Jev (2 run x 3 naskah: '
              '112 ~%d, 115 ~%d, 81 ~%d per run), wall ~2 menit.'
              % (biaya_live(), BIAYA_LIVE_PER_RUN['112'],
                 BIAYA_LIVE_PER_RUN['115'], BIAYA_LIVE_PER_RUN['81']))
        if '--ya-saya-tahu-biaya' not in argv:
            print('Berhenti: tambah --ya-saya-tahu-biaya untuk menjalankan.')
            return 2
        return jalankan_live()
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
