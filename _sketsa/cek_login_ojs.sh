#!/usr/bin/env bash
#  Apakah OJS bisa LOGIN PAKAI EMAIL? Kalau ya, user cukup ingat 1 email + 1 password.
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ① OJS bisa login pakai EMAIL? (cari kode form login) ══'
docker exec ojs-ojs_web-1 grep -rn 'usernameOrEmail\|loginByEmail\|email.*username' /var/www/html/lib/pkp/classes/user/form/LoginForm.php 2>/dev/null | head -12
echo
echo '══ ② kolom tabel users: apakah ada email? ══'
docker exec ojs-ojs_db-1 sh -c 'mysql -uroot -p\$MARIADB_ROOT_PASSWORD -N -e \"select column_name from information_schema.columns where table_name=\\\"users\\\" and column_name in (\\\"username\\\",\\\"email\\\",\\\"phone\\\");\" 2>/dev/null' 2>/dev/null | head -6
EOSSH
" 2>&1 | tail -25