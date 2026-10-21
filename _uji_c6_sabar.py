"""UJI C6 — fallback harus dipicu juga saat jalur 1 LAMBAT (bukan cuma GALAT).

KENAPA ADA (ACC Bos "1", 25Sep26):
    `_panggil_router()` dulu HANYA pindah ke jalur 2 kalau jalur 1 MELEMPAR
    GALAT. Kalau jalur 1 NYANGKUT, tidak ada yang memindahkan → mahasiswa
    menunggu 420 detik lalu dapat "Layanan AI tidak tersedia", padahal jalur 2
    sehat.

CARA UJI (BERGIGI — memanggil FUNGSI SUNGGUHAN, bukan cuma baca teks):
    Jalur 1 (`_panggil_9router`) DIGANTI tiruan yang sengaja TIDUR lama.
    Jalur 2 (`_panggil_openrouter`) DIGANTI tiruan yang jawab SEKEJAP.
    Lalu `_panggil_router()` dipanggil sungguhan dan hasilnya diperiksa:
        - dulu (sebelum C6)  → menunggu lama sekali / gagal
        - sekarang (C6)      → pindah ke jalur 2 & menjawab

    Uji ini TIDAK memakai jaringan — murni waktu + logika.
"""
import asyncio
import inspect
import re
import sys
import time

sys.path.insert(0, '/app')

lulus = gagal = 0


def cek(nama, syarat, info=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  OK   {nama}')
    else:
        gagal += 1
        print(f'  GAGAL {nama} {info}')


import app.ai as A  # noqa: E402

# ═══════════════════════════════════════════════════════════════════════════
#  🚨 PAGAR WAJIB 05Okt26 — UJI DILARANG MENGHUBUNGI HP BOS
# ═══════════════════════════════════════════════════════════════════════════
#  KEJADIAN NYATA: uji ini MEMALSUKAN jalur 1 lambat → kode notif WA SUNGGUHAN
#  (`ai.py:1107`) ikut jalan → **GOWA ASLI** → notif masuk ke HP Bos:
#     "EduAi: jalur 1 AI tidak terhubung/lambat ... tiruan/openrouter-ok"
#  Nama "tiruan/openrouter-ok" = tanda TIRUAN uji ini, BUKAN jalur 1 mati.
#  Bos sempat menanyakan: "Apakah benar? Atau palsu?"
#
#  AKAR: uji meniru perilaku jalur 1, TAPI lupa mematikan kanal WA yang
#  menjadi AKIBAT perilaku itu. Yang diuji = logika fallback, bukan WA.
#  ⇒ SELALU palsukan `wa.alarm_admin` di setiap uji yang memicu fallback.
#  (Pola sama dipakai `_uji_perilaku_wa.py` — di sana alarmnya memang diuji.)
import app.wa as _wa_nyata  # noqa: E402

_alarm_tersangka = []


def _alarm_ditahan(sebab, info=None, *a, **k):
    """Alarm WA DITAHAN — uji tidak boleh mengirim pesan ke manusia."""
    _alarm_tersangka.append({'sebab': sebab, 'model': (info or {}).get('model')})
    print(f'  [WA DITAHAN] alarm tidak dikirim · sebab={sebab!r} '
          f'model={(info or {}).get("model")!r}')


_wa_nyata.alarm_admin = _alarm_ditahan        # cukup: ai.py pakai `from . import wa`
print('  [PAGAR] alarm WA DITAHAN untuk seluruh uji ini')

KODE = open('/app/app/ai.py', encoding='utf-8').read()
KODE_BERSIH = re.sub(r'#[^\n]*', '', KODE)   # buang komentar: asersi tak boleh
                                             # lulus gara-gara kata di komentar

print('═' * 70)
print('UJI C6 — fallback dipicu GALAT *dan* LAMBAT')
print('═' * 70)

# ── 0. Konfigurasi ───────────────────────────────────────────────────────
print('\n── 0. Konfigurasi batas sabar ──')
cek('0a AI_TIMEOUT_DETIK ada (batas TOTAL)',
    hasattr(A, 'AI_TIMEOUT_DETIK'), 'tidak ada')
cek('0b BATAS_SABAR_JALUR1 ada (batas jalur 1)',
    hasattr(A, 'BATAS_SABAR_JALUR1'), 'tidak ada')
if hasattr(A, 'BATAS_SABAR_JALUR1'):
    bs = A.BATAS_SABAR_JALUR1
    cek('0c batas sabar < timeout total (masuk akal)',
        bs < A.AI_TIMEOUT_DETIK, f'{bs} vs {A.AI_TIMEOUT_DETIK}')
    cek('0d batas sabar >= 90 dtk (jangan membunuh proses SEHAT)',
        bs >= 90, f'{bs}')

# ── 1. Bukti lewat FUNGSI SUNGGUHAN ──────────────────────────────────────
print('\n── 1. Bukti perilaku: jalur 1 LAMBAT → harus pindah jalur 2 ──')

ASLI_9R = A._panggil_9router
ASLI_OR = A._panggil_openrouter
ASLI_SABAR = A.BATAS_SABAR_JALUR1
ASLI_TIMEOUT = A.AI_TIMEOUT_DETIK

jejak = {'jalur1': 0, 'jalur2': 0, 'timeout_jalur1': None, 'timeout_jalur2': None}


async def tik_9router_lambat(user_msg, timeout, **sisa):
    """Tiruan jalur 1: TIDUR melebihi batas sabar, lalu lempar TimeoutError."""
    jejak['jalur1'] += 1
    jejak['timeout_jalur1'] = timeout
    await asyncio.sleep(timeout * 1.3)
    raise asyncio.TimeoutError('tiruan: jalur 1 nyangkut')


async def tik_openrouter_cepat(user_msg, timeout, **sisa):
    """Tiruan jalur 2: jawab sekejap, seperti OpenRouter sehat."""
    jejak['jalur2'] += 1
    jejak['timeout_jalur2'] = timeout
    await asyncio.sleep(0.01)
    return '[PROFIL] tiruan jalur 2', {'model': 'tiruan/openrouter-ok',
                                       'token_in': 10, 'token_out': 10}


async def main():
    #  Batas sabar dikecilkan supaya uji cepat, TAPI perbandingannya tetap sah.
    A.BATAS_SABAR_JALUR1 = 0.4
    A._panggil_9router = tik_9router_lambat
    A._panggil_openrouter = tik_openrouter_cepat

    t0 = time.monotonic()
    konten, info = await A._panggil_router('halo', timeout=5.0)
    detik = time.monotonic() - t0
    return konten, info, detik


try:
    konten, info, detik = asyncio.run(main())
    cek('1a jalur 1 DIPANGGIL', jejak['jalur1'] == 1, jejak)
    cek('1b jalur 2 DIPANGGIL (fallback jalan walau bukan galat keras!)',
        jejak['jalur2'] == 1, jejak)
    cek('1c hasil dari jalur 2 dipakai', info.get('model') == 'tiruan/openrouter-ok', info)
    cek('1d jalur 1 diberi waktu TERBATAS (= batas sabar, bukan 5 dtk)',
        jejak['timeout_jalur1'] == 0.4, jejak['timeout_jalur1'])
    cek('1e selesai jauh sebelum timeout total (tidak menunggu 5 dtk)',
        detik < 3.0, f'{detik:.2f} dtk')
    cek('1f jalur 2 dapat sisa waktu (>0)',
        (jejak['timeout_jalur2'] or 0) > 0, jejak['timeout_jalur2'])
except Exception as e:                                          # noqa: BLE001
    cek('1a-coba jalur 1 lambat → pindah jalur 2', False, f'{type(e).__name__}: {e}')

# ── 2. Jalur 1 CEPAT → jangan ganggu (perilaku lama utuh) ────────────────
print('\n── 2. Perilaku lama: jalur 1 cepat tetap dipakai ──')
jejak2 = {'jalur1': 0, 'jalur2': 0}


async def tik_9router_cepat(user_msg, timeout, **sisa):
    jejak2['jalur1'] += 1
    await asyncio.sleep(0.01)
    return '[PROFIL] tiruan jalur 1', {'model': 'tiruan/9router-ok',
                                       'token_in': 5, 'token_out': 5}


async def tik_or_jangan_dipanggil(user_msg, timeout, **sisa):
    jejak2['jalur2'] += 1
    raise AssertionError('jalur 2 TIDAK boleh dipanggil kalau jalur 1 sehat')


async def main2():
    A.BATAS_SABAR_JALUR1 = 5.0
    A._panggil_9router = tik_9router_cepat
    A._panggil_openrouter = tik_or_jangan_dipanggil
    return await A._panggil_router('halo', timeout=5.0)


try:
    k2, i2 = asyncio.run(main2())
    cek('2a jalur 1 dipakai', jejak2['jalur1'] == 1, jejak2)
    cek('2b jalur 2 TIDAK dipanggil (tidak boros)', jejak2['jalur2'] == 0, jejak2)
    cek('2c hasil jalur 1 benar', i2.get('model') == 'tiruan/9router-ok', i2)
except Exception as e:                                          # noqa: BLE001
    cek('2a-coba jalur 1 cepat', False, f'{type(e).__name__}: {e}')

# ── 3. Jalur 1 GALAT keras → tetap pindah (perilaku lama) ────────────────
print('\n── 3. Perilaku lama: jalur 1 GALAT keras tetap pindah ──')
jejak3 = {'jalur1': 0, 'jalur2': 0}


async def tik_9router_galat(user_msg, timeout, **sisa):
    jejak3['jalur1'] += 1
    raise RuntimeError('tiruan: jalur 1 mati')


async def tik_openrouter_cepat_hitung(user_msg, timeout, kotak, **sisa):
    """Tiruan jalur 2 yang mencatat ke `kotak` yang DIMINTA (bukan global)."""
    kotak['jalur2'] += 1
    await asyncio.sleep(0.01)
    return '[PROFIL] tiruan jalur 2', {'model': 'tiruan/openrouter-ok',
                                       'token_in': 10, 'token_out': 10}


async def main3():
    A.BATAS_SABAR_JALUR1 = 5.0
    A._panggil_9router = tik_9router_galat

    async def _or(user_msg, timeout, **sisa):
        return await tik_openrouter_cepat_hitung(user_msg, timeout, jejak3)

    A._panggil_openrouter = _or
    return await A._panggil_router('halo', timeout=5.0)


try:
    k3, i3 = asyncio.run(main3())
    cek('3a jalur 1 dicoba', jejak3['jalur1'] == 1, jejak3)
    cek('3b jalur 2 dipakai', jejak3['jalur2'] >= 1, jejak3)
except Exception as e:                                          # noqa: BLE001
    cek('3a-coba jalur 1 galat', False, f'{type(e).__name__}: {e}')

# ── 4. KEDUA jalur gagal → RuntimeError (tidak diam-diam) ────────────────
print('\n── 4. Kedua jalur gagal → galat jelas ──')


async def tik_or_galat(user_msg, timeout, **sisa):
    raise RuntimeError('tiruan: openrouter mati')


async def main4():
    A.BATAS_SABAR_JALUR1 = 5.0
    A._panggil_9router = tik_9router_galat
    A._panggil_openrouter = tik_or_galat
    return await A._panggil_router('halo', timeout=5.0)


try:
    asyncio.run(main4())
    cek('4a kedua jalur gagal → RuntimeError', False, 'tidak melempar')
except RuntimeError as e:
    cek('4a kedua jalur gagal → RuntimeError', 'KEDUA jalur gagal' in str(e), str(e)[:70])
except Exception as e:                                          # noqa: BLE001
    cek('4a kedua jalur gagal → RuntimeError', False, f'{type(e).__name__}: {e}')

# ── 5. Bukti kode: pagar masih terpasang ─────────────────────────────────
print('\n── 5. Pagar masih terpasang di kode ──')
cek('5a jalur 1 dibatasi batas sabar (min(timeout, BATAS_SABAR_JALUR1))',
    'min(timeout, BATAS_SABAR_JALUR1)' in KODE_BERSIH)
cek('5b sisa waktu dihitung (timeout - waktu terpakai)',
    '_MIN_SISA_JALUR2' in KODE_BERSIH)
cek('5c log membedakan LAMBAT vs gagal',
    'LAMBAT' in KODE_BERSIH)

# ── 6. Pulihkan tiruan ───────────────────────────────────────────────────
A._panggil_9router = ASLI_9R
A._panggil_openrouter = ASLI_OR
A.BATAS_SABAR_JALUR1 = ASLI_SABAR
A.AI_TIMEOUT_DETIK = ASLI_TIMEOUT
cek('6a tiruan dipulihkan (fungsi asli kembali)',
    A._panggil_9router is ASLI_9R and A.BATAS_SABAR_JALUR1 == ASLI_SABAR)

print('\n' + '═' * 70)
print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
print('═' * 70)
sys.exit(1 if gagal else 0)
