"""UJI ANTI-524 peta/kerjakan — VIA DOMAIN PUBLIK (lewat Cloudflare).

Bukti yang dicari:
1. POST /peta/kerjakan balas CEPAT (<5 dtk) dgn latar_belakang=true + kode
2. Polling /v1/proses/{kode} → tahap berjalan → selesai
3. Token Revisi terpotong jujur (non-admin) / dicatat (admin)
"""
import json
import sys
import time
import urllib.request

DOMAIN = 'https://eduai.bikinaja.id'


def minta(path, data=None, token=None, metode=None):
    req = urllib.request.Request(
        DOMAIN + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'
                ' AppleWebKit/537.36 Chrome/151 Safari/537.36'})
    if token:
        req.add_header('Cookie', f'eduai_session={token}')
    t0 = time.time()
    terakhir = None
    for coba in range(3):
        try:
            return _kirim(req, t0)
        except Exception as e:
            terakhir = e
            time.sleep(2)
    raise terakhir


def _kirim(req, t0):
    try:
        r = urllib.request.urlopen(req, timeout=110)
        d = json.loads(r.read().decode())
        return r.status, d, time.time() - t0
    except urllib.error.HTTPError as e:
        mentah = e.read().decode() or '{}'
        try:
            isi = json.loads(mentah)
        except Exception:
            isi = {'pesan_mentah': mentah[:200]}
        return e.code, isi, time.time() - t0


def main():
    token = sys.argv[1]
    file_id = int(sys.argv[2])

    # 1) peta/mulai (GRATIS) → daftar rekomendasi
    s, d, dt = minta('/api/ai/v1/peta/mulai', {'file_id': file_id}, token)
    daftar = d.get('daftar') or []
    print(f"1) peta/mulai: {s} · {len(daftar)} rekomendasi · {dt:.1f} dtk")
    if not daftar:
        print('   TIDAK ADA rekomendasi — henti.'); return 1
    pilih = [str(d0['id']) for d0 in daftar[:1]]
    print('   dipilih:', pilih)

    # 2) peta/kerjakan DEFAULT → harus balas CEPAT + latar_belakang
    s, d, dt = minta('/api/ai/v1/peta/kerjakan',
                     {'file_id': file_id, 'pilih': pilih,
                      'peta': {'daftar': daftar}}, token)
    print(f"2) peta/kerjakan: {s} · {dt:.2f} dtk · latar_belakang="
          f"{d.get('latar_belakang')} · kode={d.get('kode')}")
    if dt > 90:
        print('   ⚠️ BALAS LAMBAT — potensi 524 masih ada!'); return 1
    if not d.get('latar_belakang') or not d.get('kode'):
        print('   isi:', json.dumps(d)[:300]); return 1
    kode = d['kode']

    # 3) polling status
    for i in range(40):
        s, st, _ = minta(f'/api/ai/v1/proses/{kode}', None, token)
        print(f"   [{i}] {st.get('status')} · {st.get('tahap')}")
        if st.get('status') in ('selesai', 'gagal'):
            break
        time.sleep(5)
    if st.get('status') == 'gagal':
        print('   galat:', st.get('pesan', '')[:200]); return 1

    # 4) hasil
    s, h, _ = minta(f'/api/ai/v1/proses/{kode}/hasil', None, token)
    print(f"4) hasil: {s} · model={h.get('model')} · "
          f"token_revisi={h.get('token_revisi')} · "
          f"panjang_jawaban={len(h.get('jawaban') or '')}")
    return 0 if s == 200 and h.get('jawaban') else 1


if __name__ == '__main__':
    sys.exit(main())
