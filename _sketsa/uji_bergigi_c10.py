import pathlib
import subprocess

BASE = pathlib.Path('/opt/data/services/eduai-publishing')
V = BASE / 'app/versi.py'
A = BASE / 'app/ai.py'
sv = V.read_text()
sa = A.read_text()
SV, SA = '/tmp/c10_versi_sehat.py', '/tmp/c10_ai_sehat.py'
pathlib.Path(SV).write_text(sv)
pathlib.Path(SA).write_text(sa)


def jalankan(label, harus_gagal_di):
    subprocess.run(['docker', 'cp', str(V), 'eduai-app:/app/app/versi.py'],
                   check=True, capture_output=True)
    subprocess.run(['docker', 'cp', str(A), 'eduai-app:/app/app/ai.py'],
                   check=True, capture_output=True)
    subprocess.run(['docker', 'restart', 'eduai-app'], capture_output=True)
    import time
    time.sleep(8)
    r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app', 'python3',
                        '_uji_c10_versi_kosong.py'], capture_output=True, text=True)
    out = r.stdout + r.stderr
    gagal = [b for b in harus_gagal_di if b in out and f'GAGAL {b}' in out]
    baris = [b for b in out.splitlines() if 'GAGAL' in b and '══' not in b]
    print(f'\n=== {label} (exit={r.returncode}) ===')
    for b in baris:
        print('   ', b.strip())
    if not baris:
        print('    ⚠️ TIDAK ADA GAGAL — pagar tidak bergigi!')
    return set(gagal)


# ── RUSAK 1: cabut pagar "layak" di simpan_versi_per_komentar ──
s1 = sv.replace("""    layak = [b for b in (blok or []) if (b.get('isi') or '').strip()]
    if not layak:""", """    layak = [b for b in (blok or []) if True]   # DIRUSAK
    if not layak:""")
assert s1 != sv, 'RUSAK-1 gagal ditulis'
V.write_text(s1)
jalankan('RUSAK 1: pagar "layak" dicabut (versi lama boleh mati)', ['2b', '2c'])

# ── RUSAK 2: cabut pagar isi kosong di simpan_versi ──
V.write_text(sv)
s2 = sv.replace("""    if not (isi or '').strip():
        log.warning('[versi] simpan_versi DITOLAK: isi kosong (file=%s bab=%s)',
                    file_id, bab)
        return None
""", """    if False:  # DIRUSAK
        return None
""")
assert s2 != sv, 'RUSAK-2 gagal ditulis'
V.write_text(s2)
jalankan('RUSAK 2: pagar isi-kosong simpan_versi dicabut', ['1a', '1b'])

# ── RUSAK 3: gear kembali HAPUS, bukan ARSIP ──
V.write_text(sv)
s3 = sv.replace("""        if not getattr(v, 'diarsipkan', False):
            v.diarsipkan = True
            n_arsip += 1""", """        db.delete(v)   # DIRUSAK: kembali menghapus
        n_arsip += 1""")
assert s3 != sv, 'RUSAK-3a gagal ditulis'
V.write_text(s3)
jalankan('RUSAK 3: gear kembali menghapus (bukan arsip)', ['4c'])

# ── RUSAK 4: daftar_versi tidak menyaring arsip ──
V.write_text(sv)
s4 = sv.replace("""    if not dengan_arsip:
        q = q.where(VersiDokumen.diarsipkan.is_(False))""",
                """    if False:  # DIRUSAK
        q = q.where(VersiDokumen.diarsipkan.is_(False))""")
assert s4 != sv, 'RUSAK-4 gagal ditulis'
V.write_text(s4)
jalankan('RUSAK 4: daftar_versi tidak saring arsip', ['4b'])

# ── RUSAK 5: pagar konten kosong di ai.py dicabut ──
V.write_text(sv)
sa5 = sa.replace("""    if not (konten or '').strip():
        log.error('[ai] C10: hasil revisi KOSONG""",
                 """    if False:  # DIRUSAK
        log.error('[ai] C10: hasil revisi KOSONG""")
assert sa5 != sa, 'RUSAK-5 gagal ditulis'
A.write_text(sa5)
jalankan('RUSAK 5: pagar ai.py (konten kosong -> 503) dicabut', ['5f'])

# ── PULIHKAN ──
V.write_text(sv)
A.write_text(sa)
print('\n=== PULIH: kembalikan kode sehat ===')
jalankan('PULIH (harus 0 gagal)', [])
