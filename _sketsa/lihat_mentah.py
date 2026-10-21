import asyncio, sys, httpx
sys.path.insert(0, '/app')
from app.ai import ROUTER_BASE, ROUTER_KEY, AI_MODEL

async def t():
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f'{ROUTER_BASE}/chat/completions',
            headers={'Authorization': f'Bearer {ROUTER_KEY}'},
            json={'model': AI_MODEL,
                  'messages': [{'role': 'user', 'content': 'Balas HANYA JSON: {"A": 5, "B": 4}'}],
                  'max_tokens': 800, 'temperature': 0.0})
    print('HTTP:', r.status_code)
    print('Content-Type:', r.headers.get('content-type'))
    print('Panjang body:', len(r.content))
    print('--- 600 byte pertama (mentah) ---')
    print(repr(r.text[:600]))
    print('--- akhir (200 byte) ---')
    print(repr(r.text[-200:]))

asyncio.run(t())
