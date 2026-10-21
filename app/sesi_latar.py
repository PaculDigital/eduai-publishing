"""(9) MAINTENANCE ONLYOFFICE — utas latar pembersih sesi basi.

Putusan Bos 24Sep26 (EDUAI 2.5 T5.4 — WAJIB): bersihkan_basi() hanya
dipanggil saat user buka halaman → sesi basi bisa menggantung selamanya.
SOLUSI: utas latar tiap 5 menit memanggil bersihkan_basi() (global,
semua user). Sesi basi = editor sudah lepas; OnlyOffice autosave sudah
menyimpan (dokumen sesi.py). RINGAN: 1 query SQL, tanpa AI.

Nada sesuai dokumen: "TAHAP 5.4 Maintenance resource OO (utas latar
pembersih — WAJIB)".
"""
import asyncio
import logging

log = logging.getLogger('eduai.sesi-latar')

JEDA_DETIK = 300    # 5 menit (sesuai dokumen T5.4)


async def _pembersih_latar():
    """Loop latar: bersihkan sesi basi tiap 5 menit (jangan matikan app)."""
    while True:
        try:
            await asyncio.sleep(JEDA_DETIK)
            from .models import SessionLocal
            from .sesi import bersihkan_basi
            db = SessionLocal()
            try:
                n = bersihkan_basi(db)
                if n:
                    log.info('[sesi-latar] %d sesi basi dibersihkan', n)
            finally:
                db.close()
        except asyncio.CancelledError:
            raise
        except Exception:                                     # noqa: BLE001
            log.exception('[sesi-latar] pembersih gagal (tidak fatal)')
            await asyncio.sleep(JEDA_DETIK)   # jangan berputar cepat kalau gagal


def mulai_pembersih(app):
    """Pasang tugas latar saat startup (dipanggil dari main._startup)."""
    app.state.tugas_pembersih_sesi = asyncio.create_task(_pembersih_latar())
    log.info('[sesi-latar] pembersih sesi basi aktif (tiap %d dtk)', JEDA_DETIK)
