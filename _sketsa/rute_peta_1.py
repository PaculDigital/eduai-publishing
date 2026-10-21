    #  ══════════════════════════════════════════════════════════════════════
    #  PETA HALUS — rekomendasi per bab + sub-bab (ACC Bos 26Sep26)
    #
    #  Kenapa ada: user perlu DIBIMBING tidak salah arah. EduAi membaca
    #  naskah sekali, lalu memberi daftar REKOMENDASI (tidak memaksa).
    #  User memilih mana yang dikerjakan -> 1 rekomendasi = 1 Token Revisi.
    #
    #  TAHAP 1 — BACA & PETA (GRATIS, putusan 13 Bos)
    #     POST /api/ai/v1/peta/mulai  {file_id | naskah, mode}
    #  TAHAP 2 — KERJAKAN pilihan user (POTONG: 1 token per rekomendasi)
    #     POST /api/ai/v1/peta/kerjakan  {file_id, pilih: ['B1.2-01', ...]}
    #
    #  PAGAR: P1 cek saldo SEBELUM potong · P2 gagal -> token kembali ·
    #  P3 anti-halusinasi (lewat ai_revisi yang sudah ada) ·
    #  P5 metode user DILARANG diubah (putusan 17).
    #  ══════════════════════════════════════════════════════════════════════

    @router.post('/v1/peta/mulai')
    async def peta_mulai(body: dict = Body(...), db: Session = Depends(get_db),
                         u: User = Depends(user_dari_cookie)) -> dict[str, Any]:
        """TAHAP 1 (GRATIS) — EduAi baca naskah lalu susun PETA HALUS."""
        from . import peta_halus as _p
        from . import state as _st

        mode = str(body.get('mode') or 'peta_awal')
        if mode not in ('peta_awal', 'revisi'):
            mode = 'peta_awal'
        pakai_ai = body.get('pakai_ai')
        pakai_ai = True if pakai_ai is None else bool(pakai_ai)

        # ── ambil teks naskah ──────────────────────────────────────────
        teks = str(body.get('naskah') or '')
        prof = None
        if not teks and body.get('file_id'):
            try:
                b = db.get(FileBerkas, int(body['file_id']))
            except Exception:
                b = None
            if not b or b.user_id != u.id:
                raise HTTPException(404, detail={'ok': False,
                                                 'pesan': 'Berkas tidak ditemukan.'})
            try:
                teks = _teks_dari_berkas(_path_berkas(b), b.nama)
            except Exception as e:
                log.warning('[peta] gagal baca berkas: %s', e)
                raise HTTPException(500, detail={
                    'ok': False, 'pesan': 'Naskah tidak bisa dibaca.'})
        if not teks.strip():
            raise HTTPException(400, detail={
                'ok': False, 'pesan': ('Belum ada naskah yang bisa dibaca. '
                                       'Unggah naskahmu dulu ya.')})

        # ── PAGAR C2: naskah tak berubah -> pakai peta lama (Rp 0) ─────
        sid = _p.sidik_naskah(teks)
        if body.get('file_id'):
            try:
                prof = (db.query(ProfilDokumen)
                          .filter(ProfilDokumen.file_id == int(body['file_id']),
                                  ProfilDokumen.user_id == u.id).first())
            except Exception:
                prof = None
            if (prof and prof.peta_sidik == sid and prof.peta_json
                    and mode == 'peta_awal'):
                try:
                    simpan = json.loads(prof.peta_json)
                    simpan['ok'] = True
                    simpan['gratis'] = True
                    simpan['dari_simpanan'] = True
                    return simpan
                except Exception:
                    pass

        # ── peta cepat (Rp 0) atau AI sungguhan ────────────────────────
        bab_state = _st.deteksi_bab_besar(teks)
        sub_state = _st.deteksi_subbab(teks, maks=40)
        bahan = _p.dari_state(bab_state, sub_state)

        info_ai: dict[str, Any] = {}
        if pakai_ai:
            ringkas = '\n'.join(f"BAB {b['bab']} — {b['judul']}" for b in bahan)
            dikirim = (ringkas + '\n\n' + teks)[:24000]
            prompt = _p.bangun_prompt(dikirim, mode=mode)
            try:
                jawab, info_ai = await _panggil_router(prompt, AI_TIMEOUT_DETIK)
                hasil = _p.rapikan_hasil_ai(_p.ambil_json(jawab), mode=mode)
            except Exception as e:
                log.warning('[peta] AI gagal -> peta cepat: %s', e)
                hasil = _p.susun(bahan, mode=mode)
                info_ai = {'jalur': 'cepat', 'galat': str(e)[:120]}
        else:
            hasil = _p.susun(bahan, mode=mode)
            info_ai = {'jalur': 'cepat'}

        # ── PAGAR C4: tidak ada temuan -> pesan ramah (sudah dirapikan) ─
        hasil['ok'] = True
        hasil['gratis'] = True
        hasil['bab_terdeteksi'] = [
            {'bab': b['bab'], 'judul': b['judul']} for b in bahan]
        hasil['sidik'] = sid
        hasil['model'] = info_ai.get('model') or info_ai.get('jalur') or ''
        hasil['pesan_kuota'] = (
            'Tahap ini GRATIS — membaca naskah tidak memakai Token Revisi. '
            'Token baru terpakai kalau kamu memilih yang dikerjakan.')

        # ── simpan peta + sidik (supaya tidak panggil AI berulang) ─────
        if body.get('file_id'):
            try:
                if prof is None:
                    prof = ProfilDokumen(file_id=int(body['file_id']),
                                         user_id=u.id, sumber='unggah')
                    db.add(prof)
                prof.peta_json = json.dumps(hasil, ensure_ascii=False)
                prof.peta_sidik = sid
                prof.peta_dibuat = _now()
                db.commit()
            except Exception as e:
                db.rollback()
                log.warning('[peta] gagal simpan peta: %s', e)

        return hasil
