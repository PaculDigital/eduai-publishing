"""Periksa sintaks JavaScript di halaman verifikasi (ekstrak <script> lalu node --check)."""
import pathlib, re, subprocess, tempfile

f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/verifikasi-loa.html')
s = f.read_text(encoding='utf-8')

scripts = re.findall(r'<script[^>]*>(.*?)</script>', s, re.S)
print('jumlah blok <script>:', len(scripts))
for i, isi in enumerate(scripts):
    if not isi.strip():
        continue
    tmp = pathlib.Path(f'/tmp/cek_js_{i}.js')
    tmp.write_text(isi, encoding='utf-8')
    r = subprocess.run(['node', '--check', str(tmp)], capture_output=True, text=True)
    print(f'  blok {i}: {len(isi)} byte -> {"OK" if r.returncode == 0 else "GAGAL"}')
    if r.returncode != 0:
        print('   ', r.stderr.strip()[:400])
