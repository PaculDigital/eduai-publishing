import os
import subprocess

r1 = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'sh', '-c',
     'for u in /app/uploads/*/; do echo "$u" $(du -s "$u" | cut -f1)KB'
     ' $(find "$u" -type f | wc -l) file; done'],
    capture_output=True, text=True)
print('══ isi /app/uploads per user ══')
print(r1.stdout)

r2 = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'sh', '-c', 'ls /app/uploads/3/ 2>/dev/null'],
    capture_output=True, text=True)
print('══ user 3 (Wulan/admin) berkasnya ══')
print(r2.stdout or '(kosong)')

r3 = subprocess.run(
    ['docker', 'inspect', 'eduai-app', '--format',
     '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{println}}{{end}}'],
    capture_output=True, text=True)
print('══ mount container ══')
print(r3.stdout)
