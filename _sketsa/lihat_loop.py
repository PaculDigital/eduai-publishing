import ast

src = open('/app/app/ai.py').read()
t = ast.parse(src)
print('=== SEMUA fungsi yg punya loop `for ... enumerate(bagian_naskah` ===')
for n in ast.walk(t):
    if isinstance(n, ast.FunctionDef):
        for b in ast.walk(n):
            if isinstance(b, ast.For) and 'bagian_naskah' in ast.unparse(b.iter):
                print(f'{n.name} baris {n.lineno}: FOR baris {b.lineno}')
                print(f'   iter: {ast.unparse(b.iter)}')
                print(f'   body ({len(b.body)}):')
                for s in b.body:
                    print(f'      {s.lineno}: {ast.unparse(s)[:85]}')
                dalam = ast.unparse(b)
                print(f'   panggil AI di dalam loop? '
                      f'{"YA" if "_revisi_dengan_failover" in dalam else "TIDAK"}')
                print(f'   end_lineno loop = {b.end_lineno}')
                print()
