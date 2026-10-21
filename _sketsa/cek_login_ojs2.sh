#!/usr/bin/env bash
#  Cari kode form login OJS — apakah terima email atau hanya username.
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ① berkas LoginForm ada di mana ══'
docker exec ojs-ojs_web-1 find /var/www/html/lib -name 'LoginForm.php' 2>/dev/null | head -4
echo
echo '══ ② cari kata kunci email di form login ══'
docker exec ojs-ojs_web-1 sh -c \"find /var/www/html/lib -name 'LoginForm.php' -exec grep -n 'username\\\|email\\\|Username\\\|orEmail' {} + 2>/dev/null\" | head -16
echo
echo '══ ③ cek database users (cara benar) ══'
docker exec ojs-ojs_db-1 printenv | grep -i -E 'mysql|maria' | head -6
EOSSH
" 2>&1 | tail -30