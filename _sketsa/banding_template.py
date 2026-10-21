import re, pathlib
for nama, path in [
    ('ZIP: template-loa-jemt.html', '/tmp/loa2_x/tridarma-loa/template-loa-jemt.html'),
    ('ZIP: agent/template-loa-jemt-agent.html', '/tmp/loa2_x/tridarma-loa/agent/template-loa-jemt-agent.html'),
    ('EduAi (sekarang)', '/opt/data/services/eduai-publishing/app/templates/loa/loa-jemt.html'),
]:
    p = pathlib.Path(path)
    if not p.exists():
        print(nama, '-> TIDAK ADA'); continue
    s = p.read_text(encoding='utf-8')
    tok = sorted(set(re.findall(r'\{\{\s*([a-zA-Z_]+)\s*\}\}', s)))
    print(f'{nama}')
    print(f'   ukuran={len(s)} byte | baris={s.count(chr(10))} | token={len(tok)} | script={"<script" in s}')
    if len(tok) < 25:
        print('   token:', ', '.join(tok))
    print()
