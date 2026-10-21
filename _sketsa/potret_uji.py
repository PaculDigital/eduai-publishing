"""POTRET halaman uji — MATA yang menilai."""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    'pc', '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

url = sys.argv[1]
keluar = sys.argv[2]
pc.potret(url, keluar, lebar=1500, tinggi=1100, tunggu=25)
print('selesai', keluar)
