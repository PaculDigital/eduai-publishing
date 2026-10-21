
kill 1240 2>/dev/null || true
sleep 2
cd /tmp/uji_root
set -a; . /tmp/.env.prod; set +a
export EDUAI_DATA_DIR=/tmp/uji_data
export EDUAI_UPLOAD_DIR=/tmp/uji_up
export PYTHONPATH=/tmp/uji_root
nohup uvicorn app.main:app --host 127.0.0.1 --port 8001 > /tmp/uji_root/server.log 2>&1 &
echo "server vitiasi pid $!"
