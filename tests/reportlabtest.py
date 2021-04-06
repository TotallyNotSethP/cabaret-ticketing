from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A8

DATA = "2 Tickets For John Doe"

if __name__ == "__main__":
    canvas = Canvas("ticket.pdf", pagesize=A8[::-1])
    canvas.drawString(0.65*inch, 1.5*inch, DATA)
    canvas.drawImage("qrcode.png", 1.05*inch, 0.5*inch, 2*cm, 2*cm)
    canvas.save()
