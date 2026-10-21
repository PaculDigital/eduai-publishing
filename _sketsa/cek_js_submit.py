"""Cek sintaks JS di submit_jurnal.html (template yang baru diubah)."""
import pathlib, re, subprocess

for nama in ['submit_jurnal.html', 'loa/verifikasi-loa.html']:
    f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates') / nama
    s = f.read_text(encoding='utf-8')
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.S)
    print(f'── {nama}: {len(scripts)} blok <script>')
    for i, isi in enumerate(scripts):
        if not isi.strip():
            continue
        tmp = pathlib.Path(f'/tmp/cek_{nama.replace("/", "_")}_{i}.js')
        tmp.write_text(isi, encoding='utf-8')
        r = subprocess.run(['node', '--check', str(tmp)], capture_output=True, text=True)
        print(f'   blok {i}: {len(isi)} byte -> {"OK" if r.returncode == 0 else "GAGAL"}')
        if r.returncode != 0:
            print('     ', r.stderr.strip()[:500])
