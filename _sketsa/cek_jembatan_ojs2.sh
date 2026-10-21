#!/usr/bin/env bash
#  ③ submit_article.php — dari mana ambil username/penulis; apakah email user dipakai?
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ③ submit_article.php — bagian penulis & username ══'
docker exec ojs-ojs_web-1 sed -n '215,290p' /var/www/html/mcp/submit_article.php
echo
echo '══ ④ KONSTANTA pagar (min kata, jendela anti-dobel) ══'
docker exec ojs-ojs_web-1 grep -nE 'define|MIN_TITLE_CHARS|MIN_ABSTRACT_WORDS|IDEMPOTENCY_WINDOW' /var/www/html/mcp/submit_article.php | head -12
EOSSH
" 2>&1 | tail -90