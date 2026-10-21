#!/usr/bin/env bash
#  ① Isi tabel users OJS (username/email) — bukti nyata
#  ② Cari form login OJS: terima email atau username?
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ① isi tabel users OJS (5 pertama) ══'
docker exec ojs-ojs_db-1 mysql -uroot -p'TridarmaOJS2026!Secure' -N -e \"select user_id, username, email from ojs.users limit 8;\" 2>/dev/null
echo
echo '══ ② form login: cari berkas template login ══'
docker exec ojs-ojs_web-1 sh -c \"grep -rln 'loginUsername' /var/www/html/lib/pkp/templates/ 2>/dev/null | head -3\"
echo '── isi labelnya ──'
docker exec ojs-ojs_web-1 sh -c \"grep -rn 'loginUsername' /var/www/html/lib/pkp/templates/user/login.tpl 2>/dev/null\" | head -8
echo
echo '══ ③ OJS cek login pakai apa? (UserDAO) ══'
docker exec ojs-ojs_web-1 sh -c \"grep -rn 'function getByUsername\|function getUserByEmail\|usernameOrEmail' /var/www/html/lib/pkp/classes/user/UserDAO.php 2>/dev/null\" | head -8
EOSSH
" 2>&1 | tail -30