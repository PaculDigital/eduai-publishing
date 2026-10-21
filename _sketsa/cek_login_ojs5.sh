#!/usr/bin/env bash
#  Cari kode LOGIN OJS yang sebenarnya (kelas LoginHandler / Auth).
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ① berkas handler login ══'
docker exec ojs-ojs_web-1 sh -c \"find /var/www/html -name '*Login*' -name '*.php' 2>/dev/null | head -10\"
echo
echo '══ ② cari 'username' di handler login (cara cek identitas) ══'
docker exec ojs-ojs_web-1 sh -c \"grep -rn 'username' /var/www/html/lib/pkp/pages/login/LoginHandler.php 2>/dev/null | head -14\"
echo
echo '══ ③ cek apakah ada dukungan EMAIL untuk login ══'
docker exec ojs-ojs_web-1 sh -c \"grep -rniE 'getUserByEmail|loginByEmail|email.*as.*username|isEmail' /var/www/html/lib/pkp/classes/user/UserDAO.php /var/www/html/lib/pkp/classes/security/Validation.php 2>/dev/null | head -10\"
EOSSH
" 2>&1 | tail -35