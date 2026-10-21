"""UJI JALUR AI EDUAI — 2 jalur, naskah nyata, prompt LENGKAP.

Menjawab pertanyaan Bos 25Sep26: "coba cek jalur yang dipakai eduai menggunakan
9router combo EduAi, dan cek fallback openrouter".

Per jalur diukur: waktu detik · NAMA MODEL ASLI · token in/out · panjang
jawaban · PATUH BENTUK PIPA atau tidak.

⚠️ Naskah = 55.440 kar (seukuran bagian nyata). Prompt LENGKAP
   (SYSTEM_REVISI + user) — bukan separuh.
"""
import asyncio
import sys
import time

sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402
import app.config as C                                                # noqa: E402

naskah = ('Penelitian ini bertujuan menguji pengaruh kualitas kehidupan kerja '
          'terhadap kinerja adaptif karyawan pada perusahaan manufaktur di '
          'Jawa Timur. Populasi penelitian ini adalah seluruh karyawan tetap. '
          ) * 280
pesan = ('[PROFIL] tesis\nNASKAH:\n' + naskah +
         '\n\nKOMENTAR:\n1. Perbaiki kalimat pertama paragraf 1.\n')

print('═' * 76)
print('  UJI JALUR AI EDUAI — naskah nyata, prompt LENGKAP')
print('═' * 76)
print(f'naskah uji    : {len(naskah):,} kar')
print(f'SYSTEM_REVISI : {len(A.SYSTEM_REVISI):,} kar')
print(f'total kirim   : {len(A.SYSTEM_REVISI) + len(pesan):,} kar')
print(f'batas sabar   : {C.BATAS_SABAR_JALUR1} dtk (jalur 1)')


def pipa(j: str) -> str:
    return 'PATUH' if A.pakai_bentuk_baru(j) else 'TIDAK PATUH'


async def jalur1():
    print('\n── JALUR 1: 9router combo `EduAi` (3 panggilan) ──')
    for i in range(1, 4):
        t = time.time()
        try:
            k, info = await A._panggil_9router(pesan, C.BATAS_SABAR_JALUR1)
            d = time.time() - t
            tanda = '✅' if d < C.BATAS_SABAR_JALUR1 else '⚠️ LEWAT BATAS'
            print(f'  #{i} {tanda} {d:6.1f} dtk · model={info.get("model")}')
            print(f'      in={info.get("token_in")} out={info.get("token_out")}'
                  f' · jawab={len(k)} kar · pipa={pipa(k)}')
        except Exception as e:                                        # noqa: BLE001
            print(f'  #{i} ❌ {time.time()-t:6.1f} dtk · '
                  f'{type(e).__name__}: {str(e)[:120]}')


async def jalur2():
    print('\n── JALUR 2: OpenRouter (4 lapis, berurutan sampai berhasil) ──')
    t = time.time()
    try:
        k, info = await A._panggil_openrouter(pesan, 240)
        print(f'  ✅ BERHASIL {time.time()-t:6.1f} dtk total · '
              f'model={info.get("model")}')
        print(f'      in={info.get("token_in")} out={info.get("token_out")}'
              f' · jawab={len(k)} kar · pipa={pipa(k)}')
    except Exception as e:                                            # noqa: BLE001
        print(f'  ❌ SEMUA LAPIS GAGAL {time.time()-t:6.1f} dtk')
        print(f'      {type(e).__name__}: {str(e)[:400]}')


async def utama():
    await jalur1()
    await jalur2()
    print('\n' + '═' * 76)


asyncio.run(utama())
