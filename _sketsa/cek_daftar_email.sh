#!/usr/bin/env bash
#  UJI NYATA: daftar user OJS dengan username = EMAIL + password default,
#  lalu LOGIN pakai email itu. Kalau berhasil -> rencana Bos PASTI jalan.
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ jembatan daftar: apakah ada pagar username (panjang/format)? ══'
docker exec ojs-ojs_web-1 grep -nE 'strlen|preg_match|username' /var/www/html/mcp/register_user.php | sed -n '1,20p'
echo
echo '══ apakah user dengan username=email sudah ada? ══'
docker exec ojs-ojs_db-1 mysql -uroot -p'TridarmaOJS2026!Secure' -N -e \"select user_id, username, email from ojs.users where username like '%@%' limit 5;\" 2>/dev/null
EOSSH
" 2>&1 | tail -30