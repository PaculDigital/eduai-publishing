
import os
# 1) siapa yang benar-benar LISTEN di 8001 (0x1F41)?
inodes = set()
for line in open('/proc/net/tcp'):
    p = line.split()
    if len(p) > 9 and p[1].endswith(':1F41') and p[3] == '0A':
        inodes.add(p[9])
print('inode listen 8001:', sorted(inodes) or 'TIDAK ADA')
pemilik = []
for p in os.listdir('/proc'):
    if not p.isdigit():
        continue
    fd_dir = f'/proc/{p}/fd'
    try:
        fds = os.listdir(fd_dir)
    except OSError:
        continue
    for fd in fds:
        try:
            lk = os.readlink(f'{fd_dir}/{fd}')
        except OSError:
            continue
        if lk.startswith('socket:[') and lk[8:-1] in inodes:
            pemilik.append(p)
            break
print('PID pemilik socket:', pemilik)
for p in pemilik:
    try:
        cmd = open(f'/proc/{p}/cmdline','rb').read().replace(b'\0', b' ').decode(errors='replace')
    except OSError:
        cmd = '?'
    print('  PID', p, '|', cmd[:220])
    try:
        print('   cwd:', os.readlink(f'/proc/{p}/cwd'))
    except OSError as e:
        print('   cwd:', e)
    try:
        env = open(f'/proc/{p}/environ','rb').read().decode(errors='replace').split('\0')
        print('   env EDUAI/PYTHONPATH:', [e[:120] for e in env if e.startswith(('EDUAI_','PYTHONPATH'))])
    except OSError as e:
        print('   env:', e)
print('--- semua proses yang mengandung uvicorn/ujiD ---')
for p in sorted(os.listdir('/proc'), key=lambda x: int(x) if x.isdigit() else 0):
    if not p.isdigit():
        continue
    try:
        cmd = open(f'/proc/{p}/cmdline','rb').read().replace(b'\0', b' ').decode(errors='replace')
    except OSError:
        continue
    if any(k in cmd for k in ('uvicorn', 'ujiD', '8001')):
        print(' ', p, '|', cmd[:220])
