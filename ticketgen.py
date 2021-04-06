def main():
    import os

    import requests
    import urllib

    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch, cm
    from reportlab.lib.pagesizes import A8

    HEADER = "TCA's Musical Theater Presents..."
    DATA = ("Tikva Peace",
            "Ticket #12 of 12",
            "Sat 5/15/21 8pm (Roof)",
            "Matata Cast")
    FOOTER = "Located At The Ritz Theater"
    LOGO_SIZE = 3.5

    response = requests.get("https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({"data": DATA}))
    with open("qrcode.png", "wb") as f:
        f.write(response.content)
    canvas = Canvas("ticket.pdf", pagesize=A8[::-1])
    canvas.drawImage("logo.jpg", 0.775 * inch, 1.15 * inch, LOGO_SIZE * cm, (907/2250) * LOGO_SIZE * cm)
    canvas.drawString(0.2 * inch, 1.8 * inch, HEADER)
    for i, string in enumerate(DATA):
        canvas.drawString((0.3 * inch) + (2 * cm), (0.975 - (0.2 * i)) * inch, string)
    canvas.drawImage("qrcode.png", 0.2 * inch, 0.35 * inch, 2 * cm, 2 * cm)
    canvas.setFillColor(HexColor("#F78D1F"))
    canvas.drawString(0.45 * inch, 0.15 * inch, FOOTER)
    canvas.save()
    os.remove("qrcode.png")


if __name__ == '__main__':
    main()
