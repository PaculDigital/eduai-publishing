"""UJI BUKU CATATAN AI (Langkah 2b-1) + PETA DOKUMEN (2b-2).

Membuktikan:
  1. catat_revisi() benar-benar MENULIS ke section_state + revisi_history
     (sebelum ini 0 baris).
  2. ringkasan_untuk_ai() mengembalikan catatan → bisa disisipkan ke prompt.
  3. AI berikutnya menerima catatan itu (tidak mengulang kerja).
  4. Peta dokumen terbentuk untuk naskah yang dipotong.

DUMMY: dipakai user/file uji, lalu DIBERSIHKAN di akhir.
    docker exec -w /app eduai-app python3 _uji_catatan_ai.py
"""
import sys

sys.path.insert(0, '/app')

from pathlib import Path                                    # noqa: E402
from app import ai as AI                                    # noqa: E402
from app import catatan_ai as C                             # noqa: E402
from app.models import (FileBerkas, RevisiHistory,          # noqa: E402
                        SectionState, SessionLocal, User)

DISERTASI = ('/app/_contoh-dokumen/disertasi-s3/'
             'DISERTASI-S3-unhas-kesehatan-stunting.docx')


def main() -> int:
    lulus = gagal = 0
    db = SessionLocal()
    fb_id = None
    print('═' * 74)
    print('UJI BUKU CATATAN AI + PETA DOKUMEN')
    print('═' * 74)

    try:
        u = db.query(User).first()
        if not u:
            print('❌ tidak ada user di DB')
            return 1
        print(f'   user uji: id={u.id} {u.email}')

        # Berkas uji (tanpa menyentuh berkas produksi)
        p = Path(DISERTASI)
        fb = FileBerkas(user_id=u.id, nama='uji-catatan-ai.docx',
                        nama_simpan='uji-catatan-ai.docx', ukuran=0,
                        tipe='application/docx')
        db.add(fb)
        db.commit()
        fb_id = fb.id
        print(f'   berkas uji: id={fb_id}')

        naskah = AI._teks_dari_berkas(p, p.name)
        print(f'   naskah: {len(naskah):,} kar → {len(AI.potong_cerdas(naskah))} bagian')

        # ── 1. catat_revisi menulis ke DB ─────────────────────────────────
        print('\n── 1. catat_revisi() menulis ke DB')
        n_sebelum = db.query(SectionState).filter_by(file_id=fb_id).count()
        hasil = C.catat_revisi(
            db, user_id=u.id, file_id=fb_id, bab='BAB I',
            komentar='Perbaiki ejaan dan tata bahasa di bagian ini.',
            naskah_sebelum=naskah[:5000],
            naskah_sesudah=naskah[:5000] + '\n\nTambahan baru untuk uji.',
            model='EduAi', konteks='bab',
        )
        n_sesudah = db.query(SectionState).filter_by(file_id=fb_id).count()
        n_hist = db.query(RevisiHistory).filter_by(file_id=fb_id).count()
        print(f'   hasil         : {hasil}')
        print(f'   section_state : {n_sebelum} → {n_sesudah} baris')
        print(f'   revisi_history: {n_hist} baris')
        ok = hasil.get('dicatat') and n_sesudah > n_sebelum and n_hist >= 1
        print(f'   {"✅ LULUS" if ok else "❌ GAGAL"}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

        # ── 2. Isi catatan benar? ─────────────────────────────────────────
        print('\n── 2. Isi catatan (sumber_terakhir harus "ai")')
        baris = C.bab_yang_sudah_direvisi(db, fb_id)
        for b in baris:
            print(f'   • {b["section_id"]} | {b["jenis_revisi"]} | '
                  f'{b["char_count"]:,} kar | sumber={b["sumber"]} | sidik={b["sidik"][:8]}')
        ok = bool(baris) and all(b['sumber'] == 'ai' for b in baris)
        print(f'   {"✅ LULUS — AI menandai dirinya sendiri" if ok else "❌ GAGAL"}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

        # ── 3. ringkasan_untuk_ai → siap disisipkan ke prompt ─────────────
        print('\n── 3. ringkasan_untuk_ai() untuk prompt AI berikutnya')
        ringkas = C.ringkasan_untuk_ai(db, fb_id)
        print(f'   panjang: {len(ringkas)} kar')
        print('   ' + ringkas[:300].replace('\n', '\n   '))
        ok = 'BAB I' in ringkas and 'JANGAN mengulang' in ringkas
        print(f'   {"✅ LULUS" if ok else "❌ GAGAL"}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

        # ── 4. Peta dokumen untuk naskah yang dipotong ────────────────────
        print('\n── 4. Peta dokumen (naskah dipotong)')
        from app.state import petakan, ringkas_peta
        peta = petakan(naskah)
        print(f'   jumlah bagian di peta: {len(peta)}')
        print('   ' + ringkas_peta(peta)[:400].replace('\n', '\n   '))
        ok = len(peta) >= 3
        print(f'   {"✅ LULUS — peta terbentuk" if ok else "❌ GAGAL"}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

        # ── 5. Sidik jari: deteksi perubahan manual user ───────────────────
        print('\n── 5. Sidik jari mendeteksi editan manual (di luar AI)')
        asli = C.sidik_isi('BAB I Pendahuluan. Latar belakang masalah.'
                           ' Penelitian ini bertujuan mengukur.')
        ubah = C.sidik_isi('BAB I Pendahuluan. Latar belakang masalah.'
                           ' Penelitian ini bertujuan MENGUKUR dan menganalisis.')
        print(f'   sidik asli : {asli}')
        print(f'   sidik ubah : {ubah}')
        ok = asli != ubah and asli != ''
        print(f'   {"✅ LULUS — perubahan manual terdeteksi" if ok else "❌ GAGAL"}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    finally:
        # BERSIHKAN jejak uji (jangan tinggalkan sampah di DB produksi)
        try:
            if fb_id:
                db.query(SectionState).filter_by(file_id=fb_id).delete()
                db.query(RevisiHistory).filter_by(file_id=fb_id).delete()
                db.query(FileBerkas).filter_by(id=fb_id).delete()
                db.commit()
                print(f'\n🧹 jejak uji dibersihkan (file_id={fb_id})')
        except Exception as e:                               # noqa: BLE001
            print(f'\n⚠️ gagal bersihkan: {e}')
        db.close()

    print('\n' + '═' * 74)
    print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
    print('═' * 74)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
