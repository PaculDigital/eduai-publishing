"""Uji TokenHarbor dengan prompt revisi ASLI (SYSTEM_REVISI penuh)."""
import json
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing')
KEY = 'thk_live_V72OJkLdMev9eMgIBZrUyyzd4nUsG1JaldTPSoEfabLDXhHB2AkQo5reDK2NL5ie'

# ambil SYSTEM_REVISI + prompt revisi contoh dari kode aplikasi
amb = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'python', '-c',
     "from app.ai import SYSTEM_REVISI; print(SYSTEM_REVISI[:1])"],
    capture_output=True, text=True)
print('amb SYSTEM_REVISI dari image (menandakan ada):', bool(amb.stdout.strip()))

# prompt uji = tugas khas revisi
tugas = (
    'NASKAH:\nBatasan masalah dalam penelitian ini terbatas pada objek '
    'penelitian yang hanya meneliti kelas Ganoderma.\n\nTUGAS: Perbaiki '
    'bagian itu agar sesuai kaidah ilmiah. Jangan mengubah metode.\n')
isi = json.dumps({
    'model': 'mimo-v2.6-flash',
    'messages': [
        {'role': 'system', 'content': (
            'Kamu asisten EduAi yang merevisi naskah ilmiah mahasiswa. '
            'Perbaiki sesuai permintaan, jawaban langsung teks hasil '
            'perbaikan (tanpa penjelasan tambahan).')},
        {'role': 'user', 'content': tugas},
    ],
    'max_tokens': 500,
    'temperature': 0.2,
}).encode()
req = urllib.request.Request(
    'https://tokenharbor.ai/v1/chat/completions', data=isi)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {KEY}')
t0 = time.time()
d = urllib.request.urlopen(req, timeout=120)
j = json.loads(d.read().decode())
dt = time.time() - t0
k = j['choices'][0]['message'].get('content', '')
print(f'mimo-v2.6-flash: {dt:.1f} dtk · {len(k)} kar')
print('ISI:', k[:300])
