# Imports
import os
import datetime
import json
import re
import typing

import requests
import urllib
import psycopg2

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A8


DATABASE_URL = "postgres://ojgkovunswhndg:9936b33ab2efff9a5091943ee8c5a31deb0b2495770e62dee7eff1b9e50cc879@ec2-18-233" \
               "-83-165.compute-1.amazonaws.com:5432/d3l2d60pufekgb"  # os.environ.get('DATABASE_URL')


def add_ticket_to_database(cast_member: str, order_number: str, ticket_number: int,
                           showtime: datetime.datetime, seating_group: str, on_roof: bool = None):
    id = json.loads(requests.get("https://www.uuidtools.com/api/generate/v4").content)[0]

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            if on_roof is not None:
                cur.execute("""INSERT INTO tickets (ticket_id, cast_member_name, order_number, ticket_number, showtime,
                                                    on_roof, seating_group)
                                            VALUES (%(id)s, %(cast_member)s, %(order_number)s, %(ticket_number)s,
                                                    %(showtime)s, %(on_roof)s, %(seating_group)s);""",
                            {"id": id, "cast_member": cast_member, "order_number": order_number,
                             "ticket_number": ticket_number, "showtime": showtime, "on_roof": on_roof,
                             "seating_group": seating_group})
            else:
                cur.execute("""INSERT INTO tickets (ticket_id, cast_member_name, order_number, ticket_number, showtime,
                                                    seating_group)
                                            VALUES (%(id)s, %(cast_member)s, %(order_number)s, %(ticket_number)s,
                                                    %(showtime)s, %(seating_group)s)""",
                            {"id": id, "cast_member": cast_member, "order_number": order_number,
                             "ticket_number": ticket_number, "showtime": showtime, "on_roof": on_roof,
                             "seating_group": seating_group})


def add_order_to_database(order_number: str, tickets_in_order):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO orders (order_number, tickets_in_order)
                                       VALUES (%(order_number)s, %(tickets_in_order)s);""",
                        {"order_number": order_number, "tickets_in_order": tickets_in_order})


def get_cast_from_showtime(showtime: datetime.datetime):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM showtimes WHERE showtime=%(showtime)s", {"showtime": showtime})
            return cur.fetchone()[1]


def gen_ticket(header: str = "TCA's Musical Theater Presents...", data: tuple[str, str, str, str] = (),
               footer: str = "Located At The Ritz Theater", copyright: str = "Ticket Created By Seth Peace",
               logo_size: typing.Union[int, float] = 3.5,
               logo: typing.Annotated[str, "filepath to image"] = "static/img/logo.jpg",
               save_to: typing.Annotated[str, "filepath to pdf (will overwrite if exists)"] = "ticket.pdf"):

    # Get QR Code
    response = requests.get("https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({"data": data}))
    with open("qrcode.png", "wb") as f:
        f.write(response.content)

    # Set Up PDF
    directory = os.path.split(save_to)[0]
    if not os.path.exists(directory):
        os.makedirs(directory)
    canvas = Canvas(save_to, pagesize=A8[::-1])

    # Draw Logo
    canvas.drawImage(logo, 0.775 * inch, 1.15 * inch, logo_size * cm, (907 / 2250) * logo_size * cm)

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
    canvas.drawString(0.37 * inch, -0.18 * inch, copyright)
    canvas.restoreState()

    # Finishing Steps
    canvas.save()
    os.remove("qrcode.png")


def gen_tickets(cast_member: str, order_number: str, showtime: datetime.datetime, seating_group: str, cast: str,
                on_roof: typing.Optional[bool], tickets_generated: int, tickets: int, formatted_showtime: str,
                total_tickets: int):
    for ticket_number in range(tickets_generated + 1, tickets_generated + tickets + 1):
        print(f"Generating Ticket #{ticket_number}/{total_tickets} For {cast_member} "
              f"(Showtime: {formatted_showtime})")

        DATA = (cast_member,
                f"Order {order_number} (#{ticket_number} of {total_tickets})",
                formatted_showtime,
                f"Group {seating_group} | {cast} Cast")

        # Call The Function Above
        formatted_order_number = f"{int(order_number):02}" if order_number.isnumeric() else f"00-{order_number}"
        gen_ticket(data=DATA, save_to=f"tickets/{formatted_order_number}/{ticket_number:02}.pdf")

        add_ticket_to_database(cast_member, order_number, ticket_number, showtime, seating_group, on_roof)


def gen_order(cast_member: str, order_number: str, showtimes: tuple[typing.Mapping[str, typing.Any], ...]):
    total_tickets = sum([showtime["tickets"] for showtime in showtimes])

    print(f"Generating {total_tickets} Tickets For {cast_member} (Order {order_number})")

    tickets_generated = 0
    for showtime in showtimes:
        formatted_showtime = re.sub(r"^0|(?<=\s)0", "", re.sub(r"(?<=[0-9])[AP]M", lambda m: m.group().lower(),
                                                               showtime["showtime"].strftime("%a %D %I%p"))) \
                             + (" (Roof)" if showtime["on_roof"] else "")
        SEATING_GROUP = "A"
        CAST = get_cast_from_showtime(showtime["showtime"])

        gen_tickets(cast_member, order_number, showtime["showtime"], SEATING_GROUP, CAST, showtime["on_roof"],
                    tickets_generated, showtime["tickets"], formatted_showtime, total_tickets)

        tickets_generated += showtime["tickets"]

    add_order_to_database(order_number, total_tickets)


if __name__ == '__main__':
    CAST_MEMBER_ = "Caleb Peace"
    ORDER_NUMBER_ = "A"
    SHOWTIMES_ = ({"showtime": datetime.datetime(2021, 5, 8, 18, 0), "on_roof": None, "tickets": 1},
                 {"showtime": datetime.datetime(2021, 5, 7, 20, 0), "on_roof": True, "tickets": 2},
                 {"showtime": datetime.datetime(2021, 5, 7, 20, 0), "on_roof": False, "tickets": 3})

    gen_order(CAST_MEMBER_, ORDER_NUMBER_, SHOWTIMES_)
