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

DATABASE_URL = "postgres://pwiakugoqqrqhe:dc057d1bd8653cc861026e8344d881d6916e40d02b78b9143218d84a1e978d82@" \
               "ec2-23-23-162-138.compute-1.amazonaws.com:5432/d8a9s7946tkonm"  # os.environ.get('DATABASE_URL')


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
        return int(self.incrementer)


def add_ticket_to_database(cast_member: str, order_number: str, ticket_number: int,
                           showtime: datetime.datetime, id_: str):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO tickets (ticket_id, cast_member_name, order_number, ticket_number, showtime)
                                        VALUES (%(id)s, %(cast_member)s, %(order_number)s, %(ticket_number)s,
                                                %(showtime)s);""",
                        {"id": id_, "cast_member": cast_member, "order_number": order_number,
                         "ticket_number": ticket_number, "showtime": showtime})


def gen_ticket(id_: str, header: str = "TCA's Musical Theater Presents...", data: tuple[str, str, str, str] = (),
               footer: str = "", copyright: str = "Ticket Created By Seth Peace",
               logo_size: typing.Union[int, float] = 3.5,
               logo: typing.Annotated[str, "filepath to image"] = "static/img/logo.jpg",
               save_to: typing.Annotated[str, "filepath to pdf (will overwrite if exists)"] = "ticket.pdf"):
    # Get QR Code
    while True:
        try:
            response = requests.get(
                "https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({"data": id_}),
                timeout=60, headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                   'Chrome/86.0.4240.75 Safari/537.36'})
        except requests.exceptions.RequestException as e:
            logging.error(f"{e}; retrying...")
        else:
            break

    with open("qrcode.png", "wb") as f:
        f.write(response.content)

    # Set Up PDF
    directory = os.path.split(save_to)[0]
    if not os.path.exists(directory) and directory != '':
        os.makedirs(directory)
    canvas = Canvas(save_to, pagesize=A8[::-1])

    # Draw Logo
    canvas.drawImage(logo, 0.77 * inch, 1.05 * inch, logo_size * cm, 0.5 * logo_size * cm)

    # Draw Header
    canvas.drawString(0.2 * inch, 1.8 * inch, header)

    # Draw Data
    for i, string in enumerate(data):
        canvas.drawString((0.3 * inch) + (2 * cm), (0.725 - (0.2 * i)) * inch, string)

    # Draw QR Code
    canvas.drawImage("qrcode.png", 0.2 * inch, 0.2 * inch, 2 * cm, 2 * cm)

    # Draw Footer
    canvas.setFillColor(HexColor("#F78D1F"))
    canvas.drawString(0.45 * inch, 0.15 * inch, footer)

    # Copyright Text
    canvas.setFont("Helvetica", 4)
    canvas.setFillColor(HexColor("#000000"))
    canvas.saveState()
    canvas.rotate(90)
    canvas.drawString(0.22 * inch, -0.18 * inch, copyright)
    canvas.restoreState()

    # Finishing Steps
    canvas.save()
    os.remove("qrcode.png")


def gen_tickets(cast_member: str, order_number: str, showtime: datetime.datetime,
                tickets_generated_in_showtime: Incrementer, tickets_total_in_showtime: Incrementer,
                tickets_generated_in_order: int, tickets: int, formatted_showtime: str, total_tickets: int):
    formatted_order_number = f"{int(order_number):02}" if order_number.isnumeric() else f"00-{order_number}"

    for ticket_number in range(int(tickets_generated_in_order + 1), int(tickets_generated_in_order + tickets + 1)):

        logging.info(f"Generating Ticket #{ticket_number}/{total_tickets} For {cast_member} "
                     f"(Showtime: {formatted_showtime})")

        tickets_generated_in_showtime.increment()

        DATA = (cast_member,
                f"Order {order_number} (#{int(tickets_generated_in_showtime)} of {int(tickets_total_in_showtime)})",
                formatted_showtime,
                "")

        # Call The Function Above
        id_ = json.loads(requests.get("https://www.uuidtools.com/api/generate/v4", timeout=60,
                                      headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                             'Chrome/86.0.4240.75 Safari/537.36'}).content)[0]
        gen_ticket(id_, data=DATA, save_to=f"tickets/{formatted_order_number}/{ticket_number:02}.pdf")

        add_ticket_to_database(cast_member, order_number, int(tickets_generated_in_showtime), showtime, id_)


def gen_order(cast_member: str, order_number: str, tickets: list[typing.Mapping[str, typing.Any], ...],
              tickets_total_in_showtimes: dict[datetime, Incrementer]):
    total_tickets = int(sum([showtime["tickets"] for showtime in tickets]))

    print()
    plural = "s" if total_tickets != 1 else ""
    logging.info(f"Generating {total_tickets} Ticket{plural} For {cast_member} (Order {order_number})")

    tickets_generated_in_order = 0
    for showtime in tickets:
        formatted_showtime = re.sub(r"^0|(?<=\s)0", "", re.sub(r"(?<=[0-9])[AP]M", lambda m: m.group().lower(),
                                                               showtime["showtime"].strftime("%a %D %I%p")))

        gen_tickets(cast_member, str(order_number), showtime["showtime"], showtime["tickets_generated"],
                    tickets_total_in_showtimes[showtime["showtime"]],
                    tickets_generated_in_order, showtime["tickets"], formatted_showtime, total_tickets)

        tickets_generated_in_order += showtime["tickets"]

    # formatted_order_number = f"{int(order_number):02}" if order_number.isnumeric() else f"00-{order_number}"
    # convert_pdfs_to_jpgs(f"tickets/{formatted_order_number}", True)


def scan_spreadsheet(spreadsheet: typing.Annotated[str, "Path to an .xlsx file"] = "static/xlsx/"
                                                                                   "CabaretTix.xlsx",
                     data_range: typing.Annotated[str, "Excel data range"] = "A2:I59"):
    SHOWTIME_INCREMENTORS = {datetime.datetime(2021, 10, 6, 14, 0): Incrementer(),
                             datetime.datetime(2021, 10, 6, 16, 0): Incrementer(),
                             datetime.datetime(2021, 10, 6, 18, 0): Incrementer(),
                             }

    TOTAL_TIX_INCREMENTORS = {datetime.datetime(2021, 10, 6, 14, 0): Incrementer(),
                              datetime.datetime(2021, 10, 6, 16, 0): Incrementer(),
                              datetime.datetime(2021, 10, 6, 18, 0): Incrementer(),
                              }

    COLUMNS = [None, "Name", None, None, None,
               datetime.datetime(2021, 10, 6, 14, 0),
               datetime.datetime(2021, 10, 6, 16, 0),
               datetime.datetime(2021, 10, 6, 18, 0),
               ]

    workbook = openpyxl.load_workbook(filename=spreadsheet)
    sheet = workbook.active
    data = sheet[data_range]

    orders = []
    order_num = 0

    for row_num, row in enumerate(data):
        order = {"cast_member": "THIS SHOULDN'T APPEAR IN PRODUCTION",
                 "order_number": (order_num := order_num + 1),
                 "tickets": []}

        for col, cell in enumerate(row):
            try:
                cell_column = COLUMNS[col]
            except IndexError:
                cell_column = None

            if cell_column == "Name":
                order["cast_member"] = cell.value
            elif isinstance(cell_column, datetime.datetime):
                order["tickets"].append({"showtime": cell_column,
                                         "tickets": cell.value,
                                         "tickets_generated": Incrementer(int(TOTAL_TIX_INCREMENTORS[cell_column])),
                                         })
                TOTAL_TIX_INCREMENTORS[cell_column].increment(cell.value)
            elif cell.value is not None:
                start_cell_loc = data_range.split(":")[0]
                if start_cell_loc[1].isnumeric():
                    row_num_offset = int(start_cell_loc[1:])
                else:
                    row_num_offset = int(start_cell_loc[0:])
                print()
                logging.warning(f"Cell with value {repr(cell.value)} ignored @ "
                                f"{string.ascii_uppercase[col]}{row_num + row_num_offset}")
        if len(order["tickets"]) > 0:
            orders.append(order)
    return orders, TOTAL_TIX_INCREMENTORS


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

    orders, tix_in_showtimes = scan_spreadsheet()

    for order in orders:
        gen_order(**order, tickets_total_in_showtimes=tix_in_showtimes)


if __name__ == '__main__':
    main()
    # gen_ticket("prettylongid", data = ("Joe Smith", "Order 0 (#0 of 0)", "I forget the date", ""))
