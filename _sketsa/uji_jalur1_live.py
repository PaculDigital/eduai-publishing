
import asyncio, time, json
from app.ai import _panggil_9router, SYSTEM_REVISI

async def jalan():
    keluar = []
    for i, tugas in enumerate([
        "Perbaiki kalimat ini: Penelitian ini bertujuan untuk bertujuan untuk menguji harga.",
        "Rapikan: Dalam hal ini penelitian yang dilakukan tersebut memberikan pengaruh yang sangat.",
        "Sederhanakan: Berdasarkan hal tersebut maka berdasarkan teori yang telah dirumuskan.",
    ], 1):
        t0 = time.monotonic()
        try:
            isi, info = await _panggil_9router(
                tugas + f" (ID uji J1-{i}-a7f)", timeout=120)
            keluar.append({"n": i, "dt": round(time.monotonic()-t0, 1),
                           "finish": info.get("finish"),
                           "reasoning": info.get("reasoning"),
                           "token_out": info.get("token_out"),
                           "panjang": len(isi),
                           "isi": isi[:110]})
        except Exception as e:
            keluar.append({"n": i, "galat": type(e).__name__ + ": " + str(e)[:160]})
    return keluar

print(json.dumps(asyncio.run(jalan()), ensure_ascii=False, indent=1))
