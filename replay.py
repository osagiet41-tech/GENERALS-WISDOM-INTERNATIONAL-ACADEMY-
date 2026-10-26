"""Paints the operations recorded by FakePdfDoc onto a reportlab canvas, so the certificate layout can be
looked at (PDF -> PNG). Approximation of pdfkit output: same coordinates, same TTF fonts, same baselines."""
import base64, io, json, sys
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

spec = json.load(open(sys.argv[1]))
W, H = spec['page']['width'], spec['page']['height']
c = canvas.Canvas(sys.argv[2], pagesize=(W, H))
for name, path in spec['fonts'].items():
    pdfmetrics.registerFont(TTFont(name, path))

def draw_segs(segs, kind):
    p = c.beginPath()
    for s in segs:
        t = s['t']
        if t == 'rect':
            p.rect(s['x'], H - s['y'] - s['h'], s['w'], s['h'])
        elif t == 'circle':
            p.circle(s['x'], H - s['y'], s['r'])
        elif t == 'poly':
            pts = s['pts']
            p.moveTo(pts[0][0], H - pts[0][1])
            for x, y in pts[1:]:
                p.lineTo(x, H - y)
            p.close()
        elif t == 'move':
            p.moveTo(s['x'], H - s['y'])
        elif t == 'line':
            p.lineTo(s['x'], H - s['y'])
    return p

for op in spec['ops']:
    if op['type'] == 'path':
        p = draw_segs(op['segs'], op['kind'])
        if op['kind'] == 'fill':
            c.setFillColor(HexColor(op['fill'])); c.drawPath(p, stroke=0, fill=1)
        else:
            c.setStrokeColor(HexColor(op['stroke'])); c.setLineWidth(op['lineWidth']); c.drawPath(p, stroke=1, fill=0)
    elif op['type'] == 'text':
        t = c.beginText()
        t.setTextOrigin(op['x'], H - op['baseline'])
        t.setFont(op['font'], op['size'])
        t.setCharSpace(op.get('cs') or 0)
        t.setFillColor(HexColor(op['fill']))
        t.textOut(op['str'])
        c.drawText(t)
    elif op['type'] == 'image':
        img = ImageReader(io.BytesIO(base64.b64decode(op['data'])))
        iw, ih = img.getSize()
        scale = min(op['w'] / iw, op['h'] / ih)
        dw, dh = iw * scale, ih * scale
        x = op['x'] + (op['w'] - dw) / 2
        y_top = op['y'] + (op['h'] - dh)  # valign bottom
        c.drawImage(img, x, H - y_top - dh, dw, dh, mask='auto')
c.showPage(); c.save()
