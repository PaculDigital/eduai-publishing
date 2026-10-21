
# ══════ 1. AWAL: belum dilewati ══════
cek('1a awal: dilewati = 0', (c1.dilewati or 0) == 0)
cek('1b awal: dilewati_pada kosong', c1.dilewati_pada is None)
a = P.ringkas(P.daftar_catatan(db, b.id))
cek('1c ringkas punya angka dilewati', a.get('dilewati') == 0, str(a))
cek('1d belum = 1 (catatan kuning)', a.get('belum') == 1, str(a))

# ══════ 2. MAHASISWA LEWATI ══════
ok, pesan = P.lewati(db, b.id, c1.id, u.id)
cek('2a lewati berhasil', ok, pesan)
db.refresh(c1)
cek('2b dilewati jadi 1', (c1.dilewati or 0) == 1)
cek('2c dilewati_pada TERISI (track history)', c1.dilewati_pada is not None)
cek('2d warna TIDAK diubah (pembimbing punya warna sendiri)',
    c1.warna == 'kuning', c1.warna)
a2 = P.ringkas(P.daftar_catatan(db, b.id))
cek('2e ringkas: dilewati = 1', a2.get('dilewati') == 1, str(a2))
cek('2f ringkas: belum = 0 (dilewati bukan "belum")',
    a2.get('belum') == 0, str(a2))
cek('2g ringkas: selesai = 0 (dilewati BUKAN selesai)',
    a2.get('selesai') == 0, str(a2))

# ══════ 3. PENJAGA: mahasiswa lain tidak bisa melewati ══════
u2 = M.User(nama='Orang Lain', email='lain@uji.id', password_hash='x',
            paket='gratis')
db.add(u2); db.commit()
ok3, pesan3 = P.lewati(db, b.id, c1.id, u2.id)
cek('3a mahasiswa lain DITOLAK', not ok3, pesan3)
cek('3b pesannya ramah (tanpa kata error/gagal)',
    'gagal' not in pesan3.lower() and 'error' not in pesan3.lower(), pesan3)

# ══════ 4. PENJAGA: tidak bisa melewati catatan orang lain ══════
ok4, pesan4 = P.lewati(db, b.id, 999999, u.id)
cek('4a catatan tidak ada → ditolak', not ok4, pesan4)

# ══════ 5. PEMBIMBING MINTA LAGI ══════
ok5, pesan5 = P.aktifkan_lagi(db, b.id, c1.id, penulis_id=7)
cek('5a pembimbing bisa minta lagi', ok5, pesan5)
db.refresh(c1)
cek('5b tanda dilewati dibersihkan di catatan LAMA', (c1.dilewati or 0) == 0)
cek('5c riwayat LAMA tetap ada (dilewati_pada TIDAK dihapus)',
    c1.dilewati_pada is not None, 'jejak hilang = melanggar track history')
cek('5d diaktifkan_pada terisi', c1.diaktifkan_pada is not None)
cek('5e diaktifkan_oleh terisi', (c1.diaktifkan_oleh or 0) == 7)

semua = P.daftar_catatan(db, b.id)
cek('5f muncul catatan BARU (ronde+1)', len(semua) == 2, f'n={len(semua)}')
baru = [c for c in semua if c.id != c1.id]
cek('5g catatan baru ada', len(baru) == 1)
if baru:
    nb = baru[0]
    cek('5h ronde baru = 2', nb.ronde == 2, str(nb.ronde))
    cek('5i menunjuk catatan lama (induk_id)', nb.induk_id == c1.id,
        f'{nb.induk_id} vs {c1.id}')
    cek('5j warna kuning (hidup lagi)', nb.warna == 'kuning', nb.warna)
    cek('5k TIDAK dilewati', (nb.dilewati or 0) == 0)
    cek('5l naskahnya sama', nb.berkas_id == c1.berkas_id)

a3 = P.ringkas(P.daftar_catatan(db, b.id))
cek('5m ringkas: dilewati = 0 lagi', a3.get('dilewati') == 0, str(a3))
#  ⚠️ KOREKSI HARAPAN 24Sep26: kepala (ronde 1) + anak (ronde 2) DUA-DUANYA
#  kuning & tidak dilewati → memang 2 yang harus dikerjakan. Wulan mula-mula
#  menulis 1 — itu SALAH WULAN, bukan cacat aplikasi.
cek('5n ringkas: belum = 2 (seluruh rantai hidup lagi)',
    a3.get('belum') == 2, str(a3))
cek('5o ringkas: total = 2', a3.get('total') == 2, str(a3))

# ══════ 6. PENJAGA: minta lagi 2× untuk catatan yang tidak dilewati ══════
ok6, pesan6 = P.aktifkan_lagi(db, b.id, c1.id, penulis_id=7)
cek('6a minta lagi untuk catatan TIDAK dilewati → ditolak', not ok6, pesan6)

# ══════ 7. LEWATI LAGI SETELAH DIMINTA ULANG ══════
target = baru[0] if baru else c1
ok7, pesan7 = P.lewati(db, b.id, target.id, u.id)
cek('7a bisa dilewati lagi', ok7, pesan7)
a4 = P.ringkas(P.daftar_catatan(db, b.id))
#  ⚠️ KOREKSI HARAPAN 24Sep26: ditandai = SELURUH RANTAI (kepala + anak) → 2.
cek('7b dilewati = 2 (seluruh rantai)', a4.get('dilewati') == 2, str(a4))
cek('7c belum = 0', a4.get('belum') == 0, str(a4))
#  Rantai: kepala (c1) + anak (baru) → keduanya harus bertanda
cek('7d SELURUH RANTAI bertanda dilewati (kepala+anak)',
    all((c.dilewati or 0) == 1 for c in P.daftar_catatan(db, b.id)))

# ══════ 8. DATA LAMA AMAN (baris tanpa kolom baru) ══════
c_lama = P.catat(db, b, 'Catatan lama tanpa kolom baru.',
                 section_id='2.1', berkas_id=f.id)
c_lama.penulis_id = u.id; db.commit()
cek('8a catatan baru langsung punya nilai default dilewati=0',
    (c_lama.dilewati or 0) == 0)
cek('8b ringkas tidak pecah dengan campuran data',
    isinstance(P.ringkas(P.daftar_catatan(db, b.id)), dict))

# ══════ 9. HASIL ══════
print()
print(f'  HASIL: {len(LULUS)} LULUS / {len(GAGAL)} GAGAL')
if GAGAL:
    for g in GAGAL:
        print(f'    - {g}')
db.close()
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if GAGAL else 0)
