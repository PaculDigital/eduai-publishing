"""UKUR: berapa token & biaya percakapan awal (niat → judul → metode)?

Tujuan: menentukan kuota percakapan baru berdasar ANGKA NYATA.
"""
import json
import subprocess
import time

K = subprocess.run(['docker', 'exec', 'eduai-app', 'printenv',
                    'EDUAI_ROUTER_KEY'], capture_output=True,
                   text=True).stdout.strip()

SYSTEM = """Anda asisten pembimbing akademik Indonesia. Tugas: menggali niat user
membuat dokumen baru sebelum menulis.

WAJIB tanyakan SATU per satu, jangan sekaligus:
1. Jenis dokumen (skripsi/tesis/proposal/perjanjian/artikel)
2. Fenomena/masalah yang diamati
3. Judul sementara
4. Metode (kuantitatif/kualitatif/campuran)

Aturan: maksimal 2 kalimat per balasan. Jangan menulis naskah sebelum 4 hal
di atas jelas. Kalau user menjawab kabur, minta perjelas."""

# Percakapan bertahap: user jawab bertahap (seperti user sungguhan)
PERCAKAPAN = [
    'saya mau bikin skripsi',
    'tentang kinerja pegawai di dinas pendidikan, kayaknya banyak yang lambat',
    'belum ada judul, bingung',
    'kuantitatif kayaknya, pakai kuesioner',
]


def kirim(messages):
    body = {'model': 'EduAi', 'messages': messages, 'max_tokens': 500,
            'temperature': 0.3, 'stream': False}
    open('/tmp/_pc.json', 'w').write(json.dumps(body))
    t0 = time.time()
    r = subprocess.run(['curl', '-s', '--max-time', '300', '-X', 'POST',
                        'http://172.17.0.1:20128/v1/chat/completions',
                        '-H', 'Content-Type: application/json',
                        '-H', 'Authorization: Bearer ' + K,
                        '-d', '@/tmp/_pc.json'],
                       capture_output=True, text=True, timeout=330)
    dt = time.time() - t0
    m = r.stdout or ''
    j = None
    try:
        j = json.loads(m)
    except Exception:
        for ln in reversed(m.splitlines()):
            if ln.startswith('data:') and '[DONE]' not in ln:
                try:
                    j = json.loads(ln[5:])
                    break
                except Exception:
                    pass
    return j, dt


print('=' * 84)
print('  UKUR PERCAKAPAN AWAL (niat -> fenomena -> judul -> metode)')
print('=' * 84)
print()
print('  {:>3}  {:>10}  {:>9}  {:>8}  {:>7}  {}'.format(
    'Ke', 'in token', 'out tok', 'Waktu', 'Total', 'Model'))
print('  ' + '-' * 78)

pesan = [{'role': 'system', 'content': SYSTEM}]
tot_in = tot_out = 0
tot_detik = 0.0
tarif = 0.005878 / 6032

for i, jawab_user in enumerate(PERCAKAPAN, 1):
    pesan.append({'role': 'user', 'content': jawab_user})
    j, dt = kirim(pesan)
    if j and 'choices' in j:
        isi = (j['choices'][0]['message'].get('content') or '').strip()
        u = j.get('usage', {})
        pt, ct = u.get('prompt_tokens', 0), u.get('completion_tokens', 0)
        tot_in += pt
        tot_out += ct
        tot_detik += dt
        print('  {:>3}  {:>10,}  {:>9,}  {:>7.1f}s  {:>7,}  {}'.format(
            i, pt, ct, dt, pt + ct, str(j.get('model', '?'))[:30]))
        print('       USER : {}'.format(jawab_user[:70]))
        print('       AI   : {}'.format(isi[:130].replace('\n', ' ')))
        pesan.append({'role': 'assistant', 'content': isi})
    else:
        print('  {:>3}  GAGAL: {}'.format(i, str(j)[:80]))

print()
print('=' * 84)
print('  TOTAL PERCAKAPAN 4 PUTARAN')
print('=' * 84)
print('  Token masuk  : {:,}'.format(tot_in))
print('  Token keluar : {:,}'.format(tot_out))
print('  Total token  : {:,}'.format(tot_in + tot_out))
print('  Waktu total  : {:.1f} detik'.format(tot_detik))
print('  BIAYA        : ${:.5f} = Rp {:,.0f}'.format(
    (tot_in + tot_out) * tarif, (tot_in + tot_out) * tarif * 16000))
print()
print('  Catatan: token MASUK naik terus tiap putaran (riwayat ikut dikirim).')
