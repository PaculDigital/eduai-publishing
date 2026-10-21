
python3 - <<'EOF'
p = '/tmp/uji_root/app/ai.py'
s = open(p).read()
lama = "'Hasil revisi belum bisa ditulis langsung ke dokumen, '"
assert s.count(lama) >= 1, 'penanda tidak ditemukan'
s = s.replace(lama, "'[VITIASI] Hasil revisi belum bisa ditulis langsung ke dokumen, '", 1)
open(p, 'w').write(s)
print('penanda [VITIASI] dipasang di salinan')
EOF
