#!/bin/bash
# Deploy perbaikan akar potongan: pasang tag baru, jalankan, verifikasi.
set -e
cd /opt/data/services/eduai-publishing
TAG_BARU="eduai-app:20260930-005819-akarpot"

echo "--- pasang tag di jalankan.sh ---"
sed -i "s|eduai-app:20260929-145342-bukti2|$TAG_BARU|" scripts/jalankan.sh
grep -oP 'eduai-app:\S+' scripts/jalankan.sh | head -2

echo "--- jalankan ---"
bash scripts/jalankan.sh 2>&1 | tail -12

echo "--- verifikasi 1: health ---"
sleep 3
curl -s -m 10 http://127.0.0.1:8000/health; echo

echo "--- verifikasi 2: md5 versi.py host vs container ---"
md5sum app/versi.py | cut -d' ' -f1
docker exec eduai-app md5sum /app/app/versi.py | cut -d' ' -f1

echo "--- verifikasi 3: isi image yang jalan ---"
docker inspect eduai-app --format 'image={{.Config.Image}} status={{.State.Status}}'
docker exec eduai-app python3 -c "
s = open('/app/app/versi.py').read()
assert '_potong_pembuka' in s and 'awal_isi_naskah' in s
print('KODE BARU ADA DI KONTAINER LAYANAN')"
