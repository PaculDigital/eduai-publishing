#!/usr/bin/env python3
"""Periksa RUTE app/main.py dengan AST yang BENAR (07 Okt 2026).

⚠️ PELAJARAN: `async def` = ast.AsyncFunctionDef, BUKAN ast.FunctionDef.
Uji Wulan sebelumnya salah tulis → lapor "POST hilang" padahal ADA.
"""
import ast
import sys

src = open('/opt/data/services/eduai-publishing/app/main.py', encoding='utf-8').read()
pohon = ast.parse(src)
rute = []
for s in ast.walk(pohon):
    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for d in s.decorator_list:
            f = d.func if isinstance(d, ast.Call) else d
            nm = getattr(f, 'attr', '')
            if nm in ('get', 'post', 'put', 'delete') and d.args:
                if isinstance(d.args[0], ast.Constant):
                    rute.append((nm.upper(), d.args[0].value, s.name,
                                 isinstance(s, ast.AsyncFunctionDef)))

print('RUTE app/main.py (AST — FunctionDef + AsyncFunctionDef):')
for m, p, fn, asink in rute:
    tanda = ' [async]' if asink else ''
    print(f'  {m:5} {p:34} -> {fn}(){tanda}')
print(f'\nTOTAL rute main.py: {len(rute)}')

konv = [r for r in rute if 'konversi' in r[1]]
print(f'\nRUTE KONVERSI: {len(konv)}')
for m, p, fn, _ in konv:
    print(f'  {m:5} {p} -> {fn}()')

ada_post = any(m == 'POST' and p == '/artikel/{fid}/konversi' for m, p, _, _ in rute)
print(f'\nPOST /artikel/{{fid}}/konversi ADA? {"YA ✅" if ada_post else "TIDAK ❌"}')

#  Pastikan endpoint API pakai wajib_login_api (401 JSON), bukan wajib_login (303).
for s in ast.walk(pohon):
    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if s.name == 'jalankan_konversi_artikel':
            teks = ast.unparse(s)
            pakai_api = 'wajib_login_api' in teks
            pakai_web = 'Depends(wajib_login)' in teks
            print(f'jalankan_konversi_artikel: pakai wajib_login_api? '
                  f'{"YA ✅" if pakai_api else "TIDAK ❌"} '
                  f'| pakai wajib_login (web)? {"YA ❌" if pakai_web else "tidak ✅"}')

sys.exit(0 if ada_post else 1)
