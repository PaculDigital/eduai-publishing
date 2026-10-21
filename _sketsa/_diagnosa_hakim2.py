"""DIAGNOSA 2: kenapa jawaban AI KOSONG? Lihat isi d['choices'] APA ADANYA.

Jangan menebak — cetak seluruh balasan mentah dari 9router.
"""
from __future__ import annotations

import asyncio
import json
import sys

import httpx

sys.path.insert(0, '/app')
from app.ai import AI_MODEL, ROUTER_BASE, ROUTER_KEY           # noqa: E402

PROMPT = ('Nilai mutu tulisan ini dengan JSON:\n'
          '{"A": <1-5>, "alasan": "<20 kata>"}\n\n'
          'TULISAN: "Rumusan masalah penelitian ini adalah apakah relationship '
          'marketing berpengaruh terhadap keputusan pembelian."')


async def main() -> None:
    print('=' * 96)
    print('DIAGNOSA 2 — isi balasan 9router APA ADANYA')
    print('=' * 96)
    print(f'ROUTER_BASE = {ROUTER_BASE}')
    print(f'AI_MODEL    = {AI_MODEL}')

    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(
            f'{ROUTER_BASE}/chat/completions',
            headers={'Authorization': f'Bearer {ROUTER_KEY}'},
            json={'model': AI_MODEL,
                  'messages': [{'role': 'user', 'content': PROMPT}],
                  'max_tokens': 300, 'temperature': 0.0})
    print(f'\nHTTP {r.status_code}')
    print(f'Content-Type: {r.headers.get("content-type")}')

    d = json.loads(r.text.split('data: [DONE]')[0].strip())
    print(f'\n──── KUNCI balasan: {list(d.keys())} ────')
    ch = d.get('choices')
    if ch:
        print(f'jumlah choices: {len(ch)}')
        print(f'kunci choice[0]: {list(ch[0].keys())}')
        print(f'finish_reason : {ch[0].get("finish_reason")}')
        pesan = ch[0].get('message') or {}
        print(f'kunci message : {list(pesan.keys())}')
        print(f'content       : {pesan.get("content")!r}')
        print(f'reasoning     : {str(pesan.get("reasoning_content") or pesan.get("reasoning") or "")[:400]!r}')
    else:
        print(f'❌ TIDAK ADA choices! Balasan penuh:')
        print(r.text[:800])
    print(f'\nusage: {d.get("usage")}')
    print('=' * 96)


asyncio.run(main())
