"""HAKIM MENTAH v2 — perbaikan 15Okt26.

🔴 AKAR YANG DIPERBAIKI (terukur, bukan tebakan):
   Model EduAi (`cb/deepseek-v4.1-flash`) adalah MODEL BERPIKIR. Dia menulis
   `reasoning_content` DULU, baru `content`. Kalau `max_tokens` habis untuk
   berpikir, balasan berhenti dengan `finish_reason='length'` dan
   `content = ''` — HAKIM MENDAPAT JAWABAN KOSONG.

   BUKTI (diukur 15Okt26, `_sketsa/_diagnosa_hakim2.py`):
     max_tokens=300 → completion_thinking_tokens=300, content='' (KOSONG)
     reasoning='Need answer in Indonesian likely... (terpotong)'

   Perbaikan:
     1. `max_tokens` dinaikkan (cukup untuk berpikir + menjawab).
     2. Kalau `content` kosong tapi `reasoning_content` ada → PAKAI ITU
        (jujur: lebih baik daripada kosong).
     3. Kalau BENAR-BENAR kosong → LEMPAR galat, jangan diam-diam menilai
        dengan angka kosong (itu yang bikin `A=? B=? C=? D=?`).

Fungsi ini HANYA untuk uji, tidak dipakai produksi.
"""
from __future__ import annotations

import json
import re
import sys

import httpx

sys.path.insert(0, '/app')
#  🚨 PELAJARAN 15Okt26 — WAJIB AMBIL SETELAN DARI PRODUKSI.
#  Kejadiannya: `_hakim_mentah.py` ditulis 24Sep (SEBELUM perbaikan
#  `enable_thinking:False` 29Sep) dan TIDAK ikut diperbarui → AI berpikir
#  lagi → jatah habis → `content` KOSONG → hakim menilai `A=? B=? C=? D=?`.
#  Produksi TIDAK rusak; yang rusak ALAT UJINYA.
#  ⇒ Setelan di bawah ini di-IMPOR dari `app.config`/`app.ai`, BUKAN ditulis
#    ulang. Kalau produksi berubah, alat uji ikut berubah otomatis.
from app.ai import AI_MODEL, AI_TIMEOUT_DETIK, ROUTER_BASE, ROUTER_KEY  # noqa: E402
from app.config import AI_MAX_TOKENS                                    # noqa: E402

#  Jatah: SAMA dengan produksi (bukan angka karangan).
MAX_TOKEN_HAKIM = AI_MAX_TOKENS
#  Setelan produksi: reasoning DIMATIKAN (ACC Bos 29Sep26, app/ai.py:966).
#  Tanpa ini, hakim akan menilai jawaban yang kosong.
ENABLE_THINKING = False


async def tanya_mentah(prompt: str, timeout: float | None = None,
                       max_tokens: int = MAX_TOKEN_HAKIM) -> tuple[str, dict]:
    """Panggil combo EduAi TANPA system revisi. Kembalikan (teks, info).

    🔴 JEBAKAN 1 (24Sep26): jawaban bisa `text/event-stream` dengan penanda
    `data: [DONE]` → JANGAN `r.json()`, pakai `r.text` + bersihkan penanda.

    🔴 JEBAKAN 2 (15Okt26): model BERPIKIR. Kalau jatah token habis untuk
    `reasoning_content`, `content` = '' dan `finish_reason` = 'length'.
    ⇒ Naikkan jatah DAN pakai `reasoning_content` sebagai cadangan.
    """
    timeout = timeout or float(AI_TIMEOUT_DETIK)
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(
            f'{ROUTER_BASE}/chat/completions',
            headers={'Authorization': f'Bearer {ROUTER_KEY}'},
            json={
                'model': AI_MODEL,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': max_tokens,
                'temperature': 0.0,
                #  🚨 SETELAN PRODUKSI — reasoning DIMATIKAN (ACC Bos 29Sep26).
                #  app/ai.py:966 & :1006 memakai ini. Alat uji WAJIB sama,
                #  kalau tidak hasil ujinya PALSU (bukan menggambarkan produksi).
                'enable_thinking': ENABLE_THINKING,
            },
        )
    if r.status_code != 200:
        raise RuntimeError(f'9router HTTP {r.status_code}: {r.text[:200]}')

    # buang penanda stream SSE sebelum parse
    mentah = r.text or ''
    mentah = mentah.split('data: [DONE]')[0]
    mentah = re.sub(r'^\s*data:\s*', '', mentah.strip(), flags=re.M)
    mentah = mentah.strip()
    try:
        d = json.loads(mentah)
    except Exception:
        # JSON mungkin terpotong — ambil objek terluar yang seimbang
        awal = mentah.find('{')
        if awal < 0:
            raise
        dalam = 0
        for i in range(awal, len(mentah)):
            if mentah[i] == '{':
                dalam += 1
            elif mentah[i] == '}':
                dalam -= 1
                if dalam == 0:
                    d = json.loads(mentah[awal:i + 1])
                    break
        else:
            raise

    ch = (d.get('choices') or [{}])[0]
    pesan = ch.get('message') or {}
    teks = pesan.get('content') or ''
    akal = pesan.get('reasoning_content') or pesan.get('reasoning') or ''

    #  🚨 JEBAKAN 2: kalau content kosong karena jatah habis untuk berpikir,
    #  pakai isi pikiran (lebih baik daripada kosong total).
    if not teks.strip() and akal.strip():
        teks = akal
        print('  [hakim] content KOSONG (finish_reason=%s) → pakai '
              'reasoning_content' % ch.get('finish_reason'))

    if not teks.strip():
        raise RuntimeError(
            'AI balas KOSONG (finish_reason=%s, thinking=%s token) — '
            'jatah token kemungkinan masih kurang'
            % (ch.get('finish_reason'),
               (d.get('usage') or {}).get('completion_thinking_tokens', '?')))

    u = d.get('usage') or {}
    info = {'token_in': u.get('prompt_tokens', 0),
            'token_out': u.get('completion_tokens', 0),
            'thinking': u.get('completion_thinking_tokens', 0),
            'finish': ch.get('finish_reason'),
            'model': d.get('model', AI_MODEL)}
    return teks, info
