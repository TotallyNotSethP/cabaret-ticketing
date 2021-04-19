# Imports
import os
import datetime
import json
import re
import typing
import string
import logging
import pathlib

import requests
import urllib
import psycopg2
import psycopg2.extras
import openpyxl
import coloredlogs
import fitz

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A8

DATABASE_URL = "postgres://ojgkovunswhndg:9936b33ab2efff9a5091943ee8c5a31deb0b2495770e62dee7eff1b9e50cc879@ec2-18-233" \
               "-83-165.compute-1.amazonaws.com:5432/d3l2d60pufekgb"  # os.environ.get('DATABASE_URL')


class Incrementer:
    def __init__(self, start_at=0):
        self.incrementer = start_at

    def increment(self, by=1):
        self.incrementer += by

    def decrement(self, by=1):
        self.incrementer -= by

    def reset(self, to=0):
        self.incrementer = to

    def __int__(self):
        return self.incrementer


def add_ticket_to_database(cast_member: str, order_number: str, ticket_number: int,
                           showtime: datetime.datetime, seating_group: str, id_: str, on_roof: bool = None):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            if on_roof is not None:
                cur.execute("""INSERT INTO tickets (ticket_id, cast_member_name, order_number, ticket_number, showtime,
                                                    on_roof, seating_group)
                                            VALUES (%(id)s, %(cast_member)s, %(order_number)s, %(ticket_number)s,
                                                    %(showtime)s, %(on_roof)s, %(seating_group)s);""",
                            {"id": id_, "cast_member": cast_member, "order_number": order_number,
                             "ticket_number": ticket_number, "showtime": showtime, "on_roof": on_roof,
                             "seating_group": seating_group})
            else:
                cur.execute("""INSERT INTO tickets (ticket_id, cast_member_name, order_number, ticket_number, showtime,
                                                    seating_group)
                                            VALUES (%(id)s, %(cast_member)s, %(order_number)s, %(ticket_number)s,
                                                    %(showtime)s, %(seating_group)s)""",
                            {"id": id_, "cast_member": cast_member, "order_number": order_number,
                             "ticket_number": ticket_number, "showtime": showtime, "on_roof": on_roof,
                             "seating_group": seating_group})


def add_order_to_database(order_number: str, tickets_in_order):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO orders (order_number, tickets_in_order)
                                       VALUES (%(order_number)s, %(tickets_in_order)s);""",
                        {"order_number": order_number, "tickets_in_order": tickets_in_order})


def get_cast_from_showtime(showtime: datetime.datetime):
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM showtimes WHERE showtime=%(showtime)s", {"showtime": showtime})
            return cur.fetchone()["cast"]


def gen_ticket(id_: str, header: str = "TCA's Musical Theater Presents...", data: tuple[str, str, str, str] = (),
               footer: str = "Located At The Ritz Theater", copyright: str = "Ticket Created By Seth Peace",
               logo_size: typing.Union[int, float] = 3.5,
               logo: typing.Annotated[str, "filepath to image"] = "static/img/logo.jpg",
               save_to: typing.Annotated[str, "filepath to pdf (will overwrite if exists)"] = "ticket.pdf"):
    # Get QR Code
    response = requests.get("https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({"data": id_}),
                            timeout=60, headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                               'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                               'Chrome/86.0.4240.75 Safari/537.36'})
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


def gen_tickets(cast_member: str, order_number: str, showtime: datetime.datetime,
                tickets_generated_in_showtime: Incrementer, cast: str, on_roof: typing.Optional[bool],
                tickets_generated_in_order: int, tickets: int, formatted_showtime: str, total_tickets: int):
    formatted_order_number = f"{int(order_number):02}" if order_number.isnumeric() else f"00-{order_number}"

    for ticket_number in range(int(tickets_generated_in_order + 1), int(tickets_generated_in_order + tickets + 1)):
        seating_group = "A" if int(tickets_generated_in_showtime) < 50 else "B"

        logging.info(f"Generating Ticket #{ticket_number}/{total_tickets} For {cast_member} "
                     f"(Showtime: {formatted_showtime})")

        DATA = (cast_member,
                f"Order {order_number} (#{ticket_number} of {total_tickets})",
                formatted_showtime,
                f"Group {seating_group} | {cast} Cast")

        # Call The Function Above
        id_ = json.loads(requests.get("https://www.uuidtools.com/api/generate/v4", timeout=60,
                                      headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                             'Chrome/86.0.4240.75 Safari/537.36'}).content)[0]
        gen_ticket(id_, data=DATA, save_to=f"tickets/{formatted_order_number}/{ticket_number:02}.pdf")

        add_ticket_to_database(cast_member, order_number, ticket_number, showtime, seating_group, id_, on_roof)

        tickets_generated_in_showtime.increment()


def gen_order(cast_member: str, order_number: str, tickets: list[typing.Mapping[str, typing.Any], ...]):
    total_tickets = int(sum([showtime["tickets"] for showtime in tickets]))

    print()
    logging.info(f"Generating {total_tickets} Tickets For {cast_member} (Order {order_number})")

    tickets_generated_in_order = 0
    for showtime in tickets:
        formatted_showtime = re.sub(r"^0|(?<=\s)0", "", re.sub(r"(?<=[0-9])[AP]M", lambda m: m.group().lower(),
                                                               showtime["showtime"].strftime("%a %D %I%p"))) \
                             + (" (Roof)" if showtime["on_roof"] else "")
        CAST = get_cast_from_showtime(showtime["showtime"])

        gen_tickets(cast_member, str(order_number), showtime["showtime"], showtime["tickets_generated"], CAST,
                    showtime["on_roof"], tickets_generated_in_order, showtime["tickets"], formatted_showtime,
                    total_tickets)

        tickets_generated_in_order += showtime["tickets"]

    formatted_order_number = f"{int(order_number):02}" if order_number.isnumeric() else f"00-{order_number}"
    convert_pdfs_to_jpgs(f"tickets/{formatted_order_number}", True)

    add_order_to_database(order_number, total_tickets)


def scan_spreadsheet(spreadsheet: typing.Annotated[str, "Path to an .xlsx file"] = "static/xlsx/"
                                                                                   "Lion King Tickets Spreadsheet.xlsx",
                     data_range: typing.Annotated[str, "Excel data range"] = "A5:Z61"):
    SHOWTIME_INCREMENTORS = {(datetime.datetime(2021, 5, 7, 16, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 7, 18, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 7, 20, 0), False): Incrementer(),
                             (datetime.datetime(2021, 5, 7, 20, 0), True): Incrementer(),
                             (datetime.datetime(2021, 5, 8, 14, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 8, 16, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 8, 18, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 8, 20, 0), False): Incrementer(),
                             (datetime.datetime(2021, 5, 8, 20, 0), True): Incrementer(),
                             (datetime.datetime(2021, 5, 9, 14, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 9, 16, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 9, 18, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 14, 16, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 14, 18, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 14, 20, 0), False): Incrementer(),
                             (datetime.datetime(2021, 5, 14, 20, 0), True): Incrementer(),
                             (datetime.datetime(2021, 5, 15, 14, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 15, 16, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 15, 18, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 15, 20, 0), False): Incrementer(),
                             (datetime.datetime(2021, 5, 15, 20, 0), True): Incrementer(),
                             (datetime.datetime(2021, 5, 16, 14, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 16, 16, 0), None): Incrementer(),
                             (datetime.datetime(2021, 5, 16, 18, 0), None): Incrementer()}
    COLUMNS = ["Name", "Order #",
               (datetime.datetime(2021, 5, 7, 16, 0), None),
               (datetime.datetime(2021, 5, 7, 18, 0), None),
               (datetime.datetime(2021, 5, 7, 20, 0), False),
               (datetime.datetime(2021, 5, 7, 20, 0), True),
               (datetime.datetime(2021, 5, 8, 14, 0), None),
               (datetime.datetime(2021, 5, 8, 16, 0), None),
               (datetime.datetime(2021, 5, 8, 18, 0), None),
               (datetime.datetime(2021, 5, 8, 20, 0), False),
               (datetime.datetime(2021, 5, 8, 20, 0), True),
               (datetime.datetime(2021, 5, 9, 14, 0), None),
               (datetime.datetime(2021, 5, 9, 16, 0), None),
               (datetime.datetime(2021, 5, 9, 18, 0), None),
               (datetime.datetime(2021, 5, 14, 16, 0), None),
               (datetime.datetime(2021, 5, 14, 18, 0), None),
               (datetime.datetime(2021, 5, 14, 20, 0), False),
               (datetime.datetime(2021, 5, 14, 20, 0), True),
               (datetime.datetime(2021, 5, 15, 14, 0), None),
               (datetime.datetime(2021, 5, 15, 16, 0), None),
               (datetime.datetime(2021, 5, 15, 18, 0), None),
               (datetime.datetime(2021, 5, 15, 20, 0), False),
               (datetime.datetime(2021, 5, 15, 20, 0), True),
               (datetime.datetime(2021, 5, 16, 14, 0), None),
               (datetime.datetime(2021, 5, 16, 16, 0), None),
               (datetime.datetime(2021, 5, 16, 18, 0), None)]

    workbook = openpyxl.load_workbook(filename=spreadsheet)
    sheet = workbook.active
    data = sheet[data_range]

    orders = []

    for row_num, row in enumerate(data):
        order = {"cast_member": "THIS SHOULDN'T APPEAR IN PRODUCTION",
                 "order_number": "THIS SHOULDN'T APPEAR IN PRODUCTION",
                 "tickets": []}
        for col, cell in enumerate(row):
            cell_column = COLUMNS[col]

            if cell_column == "Name":
                order["cast_member"] = cell.value
            elif cell_column == "Order #":
                if isinstance(cell.value, float):
                    order["order_number"] = str(int(cell.value))
                else:
                    order["order_number"] = cell.value
            elif isinstance(cell_column, tuple) \
                    and isinstance(cell_column[0], datetime.datetime) \
                    and isinstance(cell_column[1], (bool, type(None))) \
                    and isinstance(cell.value, (float, int)):
                order["tickets"].append({"showtime": cell_column[0], "on_roof": cell_column[1],
                                         "tickets": cell.value,
                                         "tickets_generated": SHOWTIME_INCREMENTORS[cell_column[0], cell_column[1]]})
            elif isinstance(cell.value, float):
                raise ValueError("Invalid Column: " + repr(cell_column))
            elif cell.value is not None:
                start_cell_loc = data_range.split(":")[0]
                if start_cell_loc[1].isnumeric():
                    row_num_offset = int(start_cell_loc[1:])
                else:
                    row_num_offset = int(start_cell_loc[0:])
                print()
                logging.warning(f"Cell with value {repr(cell.value)} ignored @ "
                                f"{string.ascii_uppercase[col]}{row_num+row_num_offset}!")
        if len(order["tickets"]) > 0:
            orders.append(order)
    return orders


def convert_pdf_to_jpg(path_to_pdf: typing.Annotated[str, "Path to a .pdf file"],
                       output_jpg: typing.Annotated[str, "Path to a .jpg file (will overwrite if exists)"]):
    pdf = fitz.open(path_to_pdf)
    page = pdf.loadPage(0)
    pixmap = page.getPixmap()
    pixmap.writePNG(output_jpg)


def convert_pdfs_to_jpgs(folder_path: typing.Annotated[str, "Path to a folder with .pdf files"],
                         delete_pdf: bool = False):
    logging.info("Converting PDFs to JPGs")
    with os.scandir(folder_path) as folder:
        for file in folder:
            file_path = pathlib.Path(file.name)
            if file_path.suffix == ".pdf":
                convert_pdf_to_jpg(os.path.join(folder_path, file_path),
                                   os.path.join(folder_path, file_path.stem + ".jpg"))
                if delete_pdf:
                    os.remove(os.path.join(folder_path, file_path))


def main():
    coloredlogs.install(level=logging.INFO,
                        fmt="%(asctime)s %(username)s@%(hostname)s "
                            "%(programname)s[%(process)d] %(levelname)s %(message)s")

    orders = scan_spreadsheet()

    for order in orders:
        gen_order(**order)


if __name__ == '__main__':
    main()
