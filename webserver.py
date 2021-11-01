# Imports
import os
import json
import datetime
import re

from flask import Flask, Response, render_template, request
import psycopg2
import psycopg2.extras

# Constants
DATABASE_URL = "postgres://pwiakugoqqrqhe:dc057d1bd8653cc861026e8344d881d6916e40d02b78b9143218d84a1e978d82@" \
               "ec2-23-23-162-138.compute-1.amazonaws.com:5432/d8a9s7946tkonm"  # os.environ.get('DATABASE_URL')

# Make A Flask App
app = Flask(__name__, template_folder="templates")


class PST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-7)

    def tzname(self, dt):
        return "PST"

    def dst(self, dt):
        return datetime.timedelta(hours=-7)


@app.route("/internals/mark_as_scanned/<id_>")
def mark_ticket_as_scanned(id_):
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE tickets SET scanned=true WHERE ticket_id=%(ticket_id)s RETURNING showtime;",
                        {"ticket_id": id_})
            showtime = cur.fetchone()
            if showtime is not None:
                cur.execute("UPDATE showtime_scan_tracker SET scans = scans + 1 WHERE showtime=%(showtime)s "
                            "RETURNING scans;", {"showtime": showtime["showtime"]})
                return Response(cur.fetchone()["scans"])  # status=204)
            else:
                return Response(status=404)


@app.route("/internals/mark_as_not_scanned/<id_>")
def mark_ticket_as_not_scanned(id_):
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE tickets SET scanned=false WHERE ticket_id=%(ticket_id)s RETURNING showtime;",
                        {"ticket_id": id_})
            showtime = cur.fetchone()
            if showtime is not None:
                cur.execute("UPDATE showtime_scan_tracker SET scans = scans + 1 WHERE showtime=%(showtime)s "
                            "RETURNING scans;", {"showtime": showtime["showtime"]})
                return Response(cur.fetchone()["scans"])  # status=204)
            else:
                return Response(status=404)


# Give The User The OS-Specific index.html.jinja2 If They Go To The Homepage
@app.route("/")
def index():
    return render_template("index.html.jinja2", platform=request.user_agent.platform.lower().strip())


# Shh! This is used on the back end to get information about a ticket.
@app.route("/internals/get_ticket/<id_>")
def get_ticket(id_):
    tickets_per_showtime = {
        datetime.datetime(2021, 11, 6, 14, 0): 209,
        datetime.datetime(2021, 11, 6, 16, 0): 226,
        datetime.datetime(2021, 11, 6, 18, 0): 315,
    }
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            # cur.execute("SELECT ticket_id, cast_member_name, o.order_number, ticket_number, s.showtime, on_roof, "
            #             "seating_group, tickets_in_order, \"cast\", scanned FROM tickets INNER JOIN orders o on "
            #             "tickets.order_number = o.order_number INNER JOIN showtimes s on tickets.showtime = s.showtime "
            #             " WHERE ticket_id=%(ticket_id)s ORDER BY tickets.order_number, ticket_number;",
            #             {"ticket_id": id_})
            cur.execute("SELECT * FROM tickets WHERE ticket_id=%(ticket_id)s", {"ticket_id": id_})
            try:
                ticket = cur.fetchone()
                showtime = datetime.datetime.fromisoformat(str(ticket["showtime"])).replace(tzinfo=PST())
                cur.execute("SELECT * FROM showtime_scan_tracker WHERE showtime=%(showtime)s",
                            {"showtime": ticket["showtime"]})
                ticket_num = cur.fetchone()
                tickets_in_showtime = tickets_per_showtime[ticket["showtime"]]
                ticket_info = "<br>".join([
                    "Name: " + str(ticket["cast_member_name"]),
                    "Showtime: " + re.sub(r"^0|(?<=\s)0", "", re.sub(r"(?<=[0-9])[AP]M",
                                                                     lambda m: m.group().lower(),
                                                                     showtime.strftime(
                                                                         "%a %m/%d/%y %I%p"))),
                    f"Scanned This Showtime: {ticket_num+1}/{tickets_in_showtime} "
                    f"({((ticket_num+1)/tickets_in_showtime)*100:.2f}%)"
                ])
                if bool(ticket["scanned"]):
                    return Response(json.dumps({"error": "ALREADY BEEN SCANNED",
                                                "color": "red",
                                                "ticket_info": ticket_info}),
                                    mimetype="application/json")
                elif not showtime - datetime.timedelta(hours=1) <= datetime.datetime.now(PST()) <= showtime + \
                         datetime.timedelta(hours=1):
                    return Response(json.dumps({"error": "WRONG SHOWTIME",
                                                "color": "red",
                                                "ticket_info": ticket_info}),
                                    mimetype="application/json")
                else:
                    mark_ticket_as_scanned(id_)
                    return Response(json.dumps({"error": "",
                                                "color": "green",
                                                "ticket_info": ticket_info}),
                                    mimetype="application/json")
            except TypeError:
                return Response(json.dumps({"error": "UNKNOWN TICKET ID",
                                            "color": "red",
                                            "ticket_info": ticket_info}),
                                mimetype="application/json")


# Runs A Development Server If You Directly Run The Script
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
