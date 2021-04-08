def main(header="TCA's Musical Theater Presents...", data=(), footer="Located At The Ritz Theater",
         copyright_="Ticket Created By Seth Peace", logo_size=3.5):
    # Import built-ins
    import os

    # Import libraries
    import requests
    import urllib

    # Import from reportlab
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch, cm
    from reportlab.lib.pagesizes import A8

    # Get QR Code
    response = requests.get("https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({"data": data}))
    with open("qrcode.png", "wb") as f:
        f.write(response.content)

    # Set Up PDF
    canvas = Canvas("ticket.pdf", pagesize=A8[::-1])

    # Draw Logo
    canvas.drawImage("logo.jpg", 0.775 * inch, 1.15 * inch, logo_size * cm, (907 / 2250) * logo_size * cm)

    # Draw Header
    canvas.drawString(0.2 * inch, 1.8 * inch, header)

    # Draw Data
    for i, string in enumerate(data):
        canvas.drawString((0.3 * inch) + (2 * cm), (0.975 - (0.2 * i)) * inch, string)

    # Draw QR Code
    canvas.drawImage("qrcode.png", 0.2 * inch, 0.35 * inch, 2 * cm, 2 * cm)

    # Draw Footer
    canvas.setFillColor(HexColor("#F78D1F"))
    canvas.drawString(0.45 * inch, 0.15 * inch, footer)

    # Copyright Text
    canvas.setFont("Helvetica", 4)
    canvas.setFillColor(HexColor("#000000"))
    canvas.saveState()
    canvas.rotate(90)
    canvas.drawString(0.37 * inch, -0.18 * inch, copyright_)
    canvas.restoreState()

    # Finishing Steps
    canvas.save()
    os.remove("qrcode.png")


# Run A Test Case If Script Run Directly
if __name__ == '__main__':
    # Constants
    HEADER = "TCA's Musical Theater Presents..."
    DATA = ("Tikva Peace",
            "Ticket #12 of 12",
            "Sat 5/15/21 8pm (Roof)",
            "Matata Cast")
    FOOTER = "Located At The Ritz Theater"
    COPYRIGHT = "Ticket Created By Seth Peace"
    LOGO_SIZE = 3.5

    # Call The Function Above
    main(header=HEADER,
         data=DATA,
         footer=FOOTER,
         copyright_=COPYRIGHT,
         logo_size=LOGO_SIZE)
