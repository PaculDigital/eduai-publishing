"""UJI NYATA: berapa token sebenarnya 1 skripsi/tesis dihabiskan?

Dokumen: TESIS_LENGKAP_Goras.docx (590.578 byte) — dokumen ASLI Bos.
Metode: ekstrak teks NYATA -> kirim ke AI lewat combo EduAi -> baca usage NYATA
        dari response (bukan hitungan teori).
"""
import json, subprocess, time, os

KEY = subprocess.run(
    ['docker','exec','eduai-app','sh','-c','grep EDUAI_ROUTER_KEY /app/.env 2>/dev/null || env | grep EDUAI_ROUTER_KEY'],
    capture_output=True, text=True).stdout.strip()
print('KEY ditemukan:', 'YA' if 'sk-' in KEY or '=' in KEY else 'TIDAK')
print(KEY[:40].replace(KEY.split('=')[-1][:8], 'XXXX') if KEY else '(kosong)')
