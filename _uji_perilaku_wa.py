"""UJI PERILAKU: apakah alarm WA benar-benar DIPANGGIL / TIDAK?

Bergigi (pola _periksa_pagar_c10.py): memotong blok keputusan WA dari
app/ai.py, MENJALANKANNYA dengan alarm palsu, lalu memeriksa panggilannya.
Bukan asersi teks — kode benar-benar dijalankan.
"""
import re
import pathlib
import sys
import types

SRC = pathlib.Path('/app/app/ai.py').read_text()

m = re.search(r'( {8}sebab1 = _sebab_jalur1\(galat1\).*?tidak terkirim: %s\', _e\))',
              SRC, re.S)
if not m:
    print('❌ blok keputusan WA TIDAK KETEMU → uji tidak berguna')
    sys.exit(1)
blok = m.group(1)

ms = re.search(r'\n    def _sebab_jalur1\(e: Exception\) -> str:.*?return \'sambungan\'.*?\n\n',
               SRC, re.S)


class _Log:
    def __init__(self):
        self.pesan = []

    def warning(self, fmt, *a):
        self.pesan.append(fmt % a if a else fmt)


def jalankan_blok(galat1, t0, jalur1_timeout, sekarang):
    """Jalankan blok keputusan WA dengan waktu tiruan. Kembalikan daftar alarm."""
    terkirim = []
    log = _Log()
    _wa = types.SimpleNamespace(alarm_admin=lambda p: terkirim.append(p))

    class _Time:
        @staticmethod
        def monotonic():
            return sekarang

    paket = types.ModuleType('app')
    paket.wa = _wa
    paket.__dict__['wa'] = _wa
    ns = {'log': log, '_wa': _wa, '__name__': 'app.ai', 'app': paket, 'info': {'model': 'glm-5.3-flash'},
          'sisa': 120.0, 't0': t0, 'jalur1_timeout': jalur1_timeout,
          'AI_MODEL': 'EduAi', 'time': _Time,
          'asyncio': types.SimpleNamespace(TimeoutError=type('T', (Exception,), {})),
          'httpx': types.SimpleNamespace(TimeoutException=type('X', (Exception,), {}))}
    exec('class _T:\n' + ''.join('    ' + b + '\n' for b in
         ms.group(0).strip().split('\n')) + '    pass', ns)
    ns['_sebab_jalur1'] = ns['_T']._sebab_jalur1
    sys.modules['app'] = paket
    pkg_ai = sys.modules.get('app.ai')
    if pkg_ai is not None:
        pkg_ai.wa = _wa
    exec('def jalankan(galat1, t0, jalur1_timeout):\n' + blok, ns)
    ns['jalankan'](galat1, t0, jalur1_timeout)
    return terkirim, log.pesan


# (nama, galat, sekarang, batas_sabar, HARUS kirim WA?)
KASUS = [
    ('model kehabisan jatah (finish=length)',
     RuntimeError('jawaban TERPOTONG (finish=length, reasoning=20, out=20/32000)'),
     100.1, 90.0, False),
    ('jawaban kosong sesaat',
     RuntimeError('konten kosong dari model'),
     100.1, 90.0, False),
    ('respons kosong dari model',
     RuntimeError("respons kosong dari model (raw='')"),
     100.1, 90.0, False),
    ('koneksi benar-benar gagal (HTTP 503)',
     RuntimeError('9router HTTP 503: service unavailable'),
     100.1, 90.0, True),
    ('alamat 9router tak ditemukan (ConnectError)',
     RuntimeError('ConnectError: [Errno -2] Name or service not known'),
     100.1, 90.0, True),
    ('jalur 1 LAMBAT (95 dtk dari batas 90)',
     RuntimeError('9router HTTP 500: gateway error'),
     195.0, 90.0, True),
    ('TimeoutError asli',
     TimeoutError('timed out'),
     100.1, 90.0, True),
]

print('═' * 100)
print('  UJI PERILAKU — alarm WA benar-benar DIPANGGIL atau TIDAK?')
print('═' * 100)
lulus = gagal = 0
for nama, g, sekarang, jt, harus in KASUS:
    terkirim, pesan_log = jalankan_blok(g, 100.0, jt, sekarang)
    nyata = len(terkirim) > 0
    ok = (nyata == harus)
    lulus += ok
    gagal += (not ok)
    print(f'  {"✅" if ok else "❌"} {nama:<46} WA={"TERKIRIM" if nyata else "tidak":<9} '
          f'(harus {"TERKIRIM" if harus else "tidak"})')
    if nyata:
        print(f'        pesan: "{terkirim[0][:92]}"')
    elif pesan_log:
        print(f'        log  : "{pesan_log[-1][:92]}"')

print()
print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
sys.exit(0 if gagal == 0 else 1)
