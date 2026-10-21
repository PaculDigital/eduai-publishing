#!/usr/bin/env bash
#  Cek 3 hal kritis untuk fitur Submit Jurnal:
#   ① register_user.php — parameter apa saja (bisa kirim password sendiri?)
#   ② submit_article.php — dari mana ambil password/username
#   ③ apakah OJS bisa login pakai password yang KITA tentukan
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ① register_user.php — parameter ══'
docker exec ojs-ojs_web-1 grep -nE 'input\\[|password|phone|username|givenName|familyName|affiliation' /var/www/html/mcp/register_user.php | head -26
echo
echo '══ ② register_user.php — apakah set password sendiri? ══'
docker exec ojs-ojs_web-1 grep -nE 'setData\\(.password|password_hash|setPassword|password' /var/www/html/mcp/register_user.php | head -12
EOSSH
" 2>&1 | tail -45