import os

import requests
import urllib

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A8

DATA = "2 Tickets For Jane Doe"

if __name__ == "__main__":
    response = requests.get("https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({"data": DATA}))
    with open("qrcode.png", "wb") as f:
        f.write(response.content)
    canvas = Canvas("ticket.pdf", pagesize=A8[::-1])
    canvas.drawString(0.65 * inch, 1.5 * inch, DATA)
    canvas.drawImage("qrcode.png", 1.05 * inch, 0.5 * inch, 2 * cm, 2 * cm)
    canvas.save()
    os.remove("qrcode.png")
