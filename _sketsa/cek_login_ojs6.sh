#!/usr/bin/env bash
#  KUNCI: Validation::login — apa yang diterima sebagai "username"? username atau email?
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ Validation::login — isinya ══'
docker exec ojs-ojs_web-1 sh -c \"grep -n 'function login' -A 40 /var/www/html/lib/pkp/classes/security/Validation.php 2>/dev/null | head -50\"
EOSSH
" 2>&1 | tail -50