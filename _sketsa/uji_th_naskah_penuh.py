"""Uji naskah penuh (42rb kar) via jalur 2 TokenHarbor — ukur waktu."""
import asyncio
import re
import time
import zipfile

from app.ai import _panggil_openrouter

with zipfile.ZipFile('/app/uploads/3/94979bfacfa7a39b.docx') as z:
    xml = z.read('word/document.xml').decode('utf-8', 'replace')
naskah = re.sub(r'<[^>]+>', '', xml)
print('panjang naskah:', len(naskah), 'kar')


async def main():
    tugas = (
        'NASKAH (bagian pendahuluan):\n' + naskah[:20000] +
        '\n\nTUGAS: Perbaiki paragraf pendahuluan agar mengalir dan ilmiah. '
        'Jangan mengubah isi/metode.')
    t0 = time.time()
    teks, info = await _panggil_openrouter(tugas, timeout=300)
    dt = time.time() - t0
    print(f'mimo-v2.6-flash: OK {dt:.1f} dtk · keluar {len(teks)} kar')
    print('awal jawaban:', teks[:150].replace('\n', ' '))


asyncio.run(main())
