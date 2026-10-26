"""Login ulang Scite MCP (OAuth + PKCE + DCR) — penangkap kode OTOMATIS.

Alur (terbukti 13 Okt 2026, diulang 26 Okt 2026 karena access+refresh token
sama-sama kedaluwarsa):

  1. Baca metadata OAuth Scite (/.well-known/oauth-protected-resource
     lalu /.well-known/oauth-authorization-server).
  2. Daftarkan klien BARU (DCR /register).
     ⚠️ WAJIB klien baru tiap ganti alamat terowongan: redirect_uri terikat
     ke klien. Klien lama (127.0.0.1) DITOLAK di alamat tunnel.
  3. Bangun tautan otorisasi + PKCE (S256). Tautan DIBERIKAN ke Bos;
     BOS yang mengetik email/password — skrip ini TIDAK menyimpan password.
  4. Bos login -> Scite balik ke /callback -> kode ditangkap SENDIRI
     (nol salin-tempel) -> ditukar jadi access_token + refresh_token.
  5. Token disimpan ke .env (bukan dicetak) + berkas hasil lokal.

Pakai:
    python3 _sketsa/login_scite_oauth.py --alamat https://xxx.trycloudflare.com

HANYA SATU proses login boleh hidup — dua proses = state mismatch.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8791
STATE = {}
HASIL = {'kode': None, 'galat': None, 'selesai': threading.Event()}


def _get(url):
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=30))


def _post(url, data, ctype='application/json'):
    badan = json.dumps(data).encode() if ctype == 'application/json' else data
    req = urllib.request.Request(url, data=badan, headers={'Content-Type': ctype,
                                                           'Accept': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=30))


class Penangkap(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path == '/callback':
            st_datang = q.get('state', [''])[0]
            #  ⚠️ WAJIB cocokkan state. Tanpa ini, siapa pun yang menembak
            #  /callback (mis. curl uji) langsung MENUTUP proses login
            #  (kejadian nyata 26 Okt 2026: `curl .../callback?uji=1`
            #  membuat skrip berhenti dengan "GAGAL: ?").
            if st_datang != STATE.get('state'):
                self.send_response(400)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'state tidak cocok - abaikan, login tetap jalan.')
                return
            if 'code' in q:
                HASIL['kode'] = q['code'][0]
                pesan = 'Login berhasil. Kode ditangkap. Tutup tab ini.'
            else:
                HASIL['galat'] = q.get('error_description', q.get('error', ['?']))[0]
                pesan = 'Login GAGAL: ' + HASIL['galat']
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(('<html><body style="font-family:sans-serif;padding:40px">'
                              f'<h2>{pesan}</h2></body></html>').encode())
            HASIL['selesai'].set()
        else:
            self.send_response(404)
            self.end_headers()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--alamat', required=True,
                    help='alamat publik terowongan, mis. https://xxx.trycloudflare.com')
    arg = ap.parse_args()
    dasar = arg.alamat.rstrip('/')
    redirect = dasar + '/callback'

    print('[1] baca metadata OAuth Scite…')
    prm = _get('https://api.scite.ai/.well-known/oauth-protected-resource')
    izin = (prm.get('authorization_servers') or ['https://api.scite.ai'])[0]
    md = _get(izin.rstrip('/') + '/.well-known/oauth-authorization-server')
    reg = md.get('registration_endpoint')
    otor = md.get('authorization_endpoint')
    token_ep = md.get('token_endpoint')
    print('    otorisasi :', otor)
    print('    token     :', token_ep)
    print('    daftar    :', reg)

    print('[2] daftarkan klien BARU (DCR) untuk alamat terowongan ini…')
    klien = _post(reg, {
        'client_name': 'EduAi Publishing (login ulang)',
        'redirect_uris': [redirect],
        'grant_types': ['authorization_code', 'refresh_token'],
        'response_types': ['code'],
        'token_endpoint_auth_method': 'none',
    })
    cid = klien['client_id']
    print('    client_id :', cid)

    print('[3] bangun tautan otorisasi + PKCE…')
    verif = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip('=')
    tantang = base64.urlsafe_b64encode(
        hashlib.sha256(verif.encode()).digest()).decode().rstrip('=')
    st = secrets.token_urlsafe(24)
    STATE['state'] = st
    qs = urllib.parse.urlencode({
        'response_type': 'code', 'client_id': cid, 'redirect_uri': redirect,
        'state': st, 'code_challenge': tantang, 'code_challenge_method': 'S256',
        'scope': 'mcp offline_access',
    })
    tautan = otor + '?' + qs

    srv = HTTPServer(('0.0.0.0', PORT), Penangkap)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    print('\n' + '=' * 66)
    print('TAUTAN LOGIN — buka di browser Bos, login SENDIRI:')
    print(tautan)
    print('=' * 66)
    print(f'(menunggu balasan di {redirect})')

    if not HASIL['selesai'].wait(600):
        print('WAKTU HABIS (10 menit) — tidak ada balasan.')
        srv.shutdown()
        return 1
    srv.shutdown()
    if HASIL['galat']:
        print('GAGAL:', HASIL['galat'])
        return 1

    print('[4] tukar kode jadi token…')
    badan = urllib.parse.urlencode({
        'grant_type': 'authorization_code', 'code': HASIL['kode'],
        'client_id': cid, 'redirect_uri': redirect, 'code_verifier': verif,
    }).encode()
    d = json.load(urllib.request.urlopen(urllib.request.Request(
        token_ep, data=badan,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}),
        timeout=40))
    print('    SUKSES — berlaku', d.get('expires_in'), 'detik')
    print('    ada refresh_token?', bool(d.get('refresh_token')))

    # simpan: token TIDAK dicetak
    hasil = {'access_token': d['access_token'],
             'refresh_token': d.get('refresh_token'),
             'client_id': cid, 'token_endpoint': token_ep,
             'alamat': dasar, 'redirect': redirect,
             'expires_in': d.get('expires_in')}
    os.makedirs('/opt/data/.rahasia-scite', exist_ok=True)
    p = '/opt/data/.rahasia-scite/token-scite.json'
    with open(p, 'w') as f:
        json.dump(hasil, f, indent=1)
    os.chmod(p, 0o600)
    print('[5] token disimpan ke', p, '(mode 600)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
