import fitz, pathlib
# ══ uji QR bisa DIBACA (bukan cuma gambar tempelan) ══
d = fitz.open('/tmp/uji_loa28/loa.pdf')
pg = d[0]
try:
    import PIL.Image as Image
    for info in pg.get_images(full=True):
        xref = info[0]
        pix = fitz.Pixmap(d, xref)
        if pix.width < 200:      # QR kecil
            pix.save('/tmp/uji_loa28/qr_saja.png')
            print('QR tersimpan:', pix.width, 'x', pix.height)
except Exception as e:
    print('gagal simpan QR:', e)

# coba baca QR pakai pyzbar kalau ada
try:
    from pyzbar.pyzbar import decode
    from PIL import Image
    hasil = decode(Image.open('/tmp/uji_loa28/qr_saja.png'))
    print('HASIL BACA QR:', [h.data.decode() for h in hasil])
except ImportError:
    print('pyzbar tidak ada — pakai cara lain')
