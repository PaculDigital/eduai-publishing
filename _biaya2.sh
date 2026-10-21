#!/bin/bash
# Cek saldo & biaya dari panel 9router (admin)
KUNCI=$(docker exec eduai-app printenv EDUAI_ROUTER_KEY 2>/dev/null)
echo "═══ Cek endpoint saldo ═══"
for u in /me/usage /api/me/usage /me /usage /key/info; do
  printf "  %-18s " "$u"
  code=$(curl -s -o /tmp/_bd.json -w "%{http_code}" --max-time 12 \
    "http://172.17.0.1:20128$u" -H "Authorization: Bearer $KUNCI")
  echo "HTTP $code $(head -c 120 /tmp/_bd.json 2>/dev/null | tr -d '\n')"
done
echo
echo "═══ Panel admin 9router (port lain?) ═══"
for p in 20128 3000 8080 8317; do
  printf "  port %-6s " "$p"
  curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 "http://172.17.0.1:$p/" 2>/dev/null
done