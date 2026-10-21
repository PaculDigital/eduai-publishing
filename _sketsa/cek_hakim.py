import asyncio, sys, traceback, json
sys.path.insert(0, '/app')
from _hakim_mentah import tanya_mentah

async def t():
    try:
        teks, info = await tanya_mentah('Balas HANYA JSON: {"A": 5, "B": 4}')
        print('OK TEKS:', repr(teks[:300]))
        print('OK INFO:', info)
    except Exception as e:
        print('GAGAL:', type(e).__name__, str(e)[:300])
        traceback.print_exc()

asyncio.run(t())
