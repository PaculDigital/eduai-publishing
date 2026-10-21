    @router.post('/v1/peta/kerjakan')
    async def peta_kerjakan(body: dict = Body(...), db: Session = Depends(get_db),
                            u: User = Depends(user_dari_cookie)) -> dict[str, Any]:
        """TAHAP 2 (POTONG) — kerjakan rekomendasi yang DIPILIH user.

        Potongan: 1 Token Revisi per rekomendasi (ACC Bos 26Sep26).
        PAGAR P1: saldo dicek SEBELUM potong (jangan potong lalu gagal).
        PAGAR P2: gagal / hasil kosong -> token DIKEMBALIKAN.
        PAGAR C1: yang dikerjakan ditandai supaya tidak ditawarkan lagi.
        """
        from .kuota import saldo_token, potong_banyak, kembalikan_banyak

        pilih = [str(x) for x in (body.get('pilih') or []) if str(x).strip()]
        if not pilih:
            return {'ok': False, 'kode': 'belum_pilih',
                    'pesan': ('Pilih dulu bagian yang mau dirapikan — centang '
                              'rekomendasi yang kamu setujui.')}

        peta = body.get('peta') or {}
        daftar = peta.get('daftar') or []
        mau = [d for d in daftar if str(d.get('id')) in set(pilih)]
        if not mau:
            return {'ok': False, 'kode': 'peta_tidak_cocok',
                    'pesan': ('Rekomendasi yang dipilih tidak ditemukan di peta. '
                              'Muat ulang peta dulu ya.')}

        # ── PAGAR P1: cek saldo DULU ───────────────────────────────────
        butuh = len(mau)                     # 1 rekomendasi = 1 token
        saldo = saldo_token(db, u)
        if saldo < butuh:
            return {'ok': False, 'kode': 'saldo_kurang',
                    'butuh': butuh, 'saldo': saldo, 'kurang': butuh - saldo,
                    'pesan': (f'Perlu {butuh} Token Revisi, sedangkan saldomu '
                              f'{saldo} (kurang {butuh - saldo}).')}

        info_potong = potong_banyak(db, u, butuh)
        if info_potong.get('ok') is False:
            return info_potong

        # ── susun tugas untuk AI (hanya bagian yang dipilih) ───────────
        tugas = []
        for d in mau:
            sub = f"{d.get('bab')}.{d.get('subbab')}" if d.get('subbab') else str(d.get('bab'))
            tugas.append(f"- [{sub}] {d.get('masalah')}"
                         + (f" -> {d.get('saran')}" if d.get('saran') else ''))
        perintah = (
            'Perbaiki HANYA bagian-bagian berikut pada naskah. Jangan menulis '
            'ulang bagian lain. Metode penelitian penulis (jumlah sampel, '
            'teknik sampling, instrumen, skala, teknik analisis, definisi '
            'operasional, model) DILARANG diubah.\n' + '\n'.join(tugas))

        hasil_kerja: dict[str, Any] = {}
        try:
            hasil_kerja = await ai_revisi(
                body={'file_id': body.get('file_id'),
                      'permintaan': perintah,
                      'intent': 'perkaya'},
                db=db, u=u)
        except Exception as e:
            kembalikan_banyak(db, u, butuh)          # PAGAR P2
            log.error('[peta] kerjakan gagal: %s', e)
            raise HTTPException(503, detail={
                'ok': False,
                'pesan': (f'Gagal mengerjakan: {e}. Token Revisimu sudah '
                          'dikembalikan.'),
                'kuota_dikembalikan': True})

        # ── PAGAR P2: hasil kosong / tidak wajar -> token kembali ──────
        if (not hasil_kerja
                or hasil_kerja.get('kode') in ('hasil_kosong',
                                               'jawaban_tidak_wajar')
                or hasil_kerja.get('ok') is False):
            kembalikan_banyak(db, u, butuh)
            return {'ok': False, 'kode': 'hasil_kosong',
                    'pesan': ('Bagian itu belum bisa dirapikan. Token Revisimu '
                              'sudah dikembalikan — coba pilih yang lain.'),
                    'kuota_dikembalikan': True}

        # ── PAGAR C1: tandai sudah ditawarkan (jangan tawarkan lagi) ───
        if body.get('file_id'):
            try:
                prof = (db.query(ProfilDokumen)
                          .filter(ProfilDokumen.file_id == int(body['file_id']),
                                  ProfilDokumen.user_id == u.id).first())
                if prof and prof.peta_json:
                    lama = json.loads(prof.peta_json)
                    sudah = set(lama.get('sudah_ditawarkan') or [])
                    sudah |= set(pilih)
                    lama['sudah_ditawarkan'] = sorted(sudah)
                    lama['daftar'] = [d for d in (lama.get('daftar') or [])
                                      if str(d.get('id')) not in set(pilih)]
                    lama['jumlah'] = len(lama['daftar'])
                    prof.peta_json = json.dumps(lama, ensure_ascii=False)
                    db.commit()
            except Exception as e:
                db.rollback()
                log.warning('[peta] gagal tandai tawaran: %s', e)

        hasil_kerja['ok'] = True
        hasil_kerja['dikerjakan'] = pilih
        hasil_kerja['token_dipotong'] = butuh
        hasil_kerja['saldo_sebelum'] = info_potong.get('saldo_sebelum')
        hasil_kerja['saldo_sesudah'] = info_potong.get('saldo_sesudah')
        return hasil_kerja
