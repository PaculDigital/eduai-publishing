"""Intip balasan MENTAH 9router (tanpa parse) — kenapa JSONDecodeError?"""
import base64
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('uji_c7', '_uji_publik_komentar.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

py = (
    "import os, json, urllib.request as u\n"
    "isi = json.dumps({'model': 'EduAi', 'messages': [{'role': 'user',"
    " 'content': 'Balas: OK'}], 'max_tokens': 16, 'temperature': 0.2}).encode()\n"
    "r = u.Request('http://9router:20128/v1/chat/completions', data=isi,\n"
    "  headers={'Authorization': 'Bearer ' + os.environ.get('EDUAI_ROUTER_KEY', ''),"
    " 'Content-Type': 'application/json'}, method='POST')\n"
    "b = u.urlopen(r, timeout=45).read()\n"
    "print('PANJANG=', len(b))\n"
    "print('KEPALA=', repr(b[:150]))\n"
    "print('EKOR=', repr(b[-250:]))\n"
)
b64 = base64.b64encode(py.encode()).decode()
rc, out = mod._docker(
    'docker exec eduai-app python3 -c '
    + '"import base64;exec(base64.b64decode(\'' + b64 + '\'))"')
print('rc=', rc)
print(out[:1500])
sys.exit(0)
