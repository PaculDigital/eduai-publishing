#!/usr/bin/env bash
#  Cari template form login OJS yang BENAR (di mana pun) + cek apakah terima email.
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ① semua berkas login*.tpl ══'
docker exec ojs-ojs_web-1 sh -c \"find /var/www/html -name 'login*.tpl' 2>/dev/null | head -8\"
echo
echo '══ ② cari kata kunci di template login ══'
docker exec ojs-ojs_web-1 sh -c \"find /var/www/html -name 'login*.tpl' -exec grep -Hn 'username\\\|email' {} + 2>/dev/null\" | head -14
echo
echo '══ ③ UserDAO: fungsi pencarian user ══'
docker exec ojs-ojs_web-1 sh -c \"grep -n 'function get\|username' /var/www/html/lib/pkp/classes/user/UserDAO.php 2>/dev/null\" | head -12
EOSSH
" 2>&1 | tail -35