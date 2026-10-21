import subprocess

cd = 'cd /opt/data/services/eduai-publishing && '
print('══ 1. JS mulai.html: API yang dipanggil ══')
print(subprocess.run(
    cd + "grep -o 'alur/[a-z-]*' app/templates/mulai.html | sort -u",
    shell=True, capture_output=True, text=True).stdout)
print('══ 2. uji_alur: rute yang diuji ══')
print(subprocess.run(
    cd + "grep -n 'def uji\\|UJI ' _sketsa/uji_alur_awal.py | head -20",
    shell=True, capture_output=True, text=True).stdout)
