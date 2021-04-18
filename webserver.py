# Imports
import os
import json

from flask import Flask, Response, render_template
import psycopg2
import psycopg2.extras


# Constants
DATABASE_URL = os.environ.get('DATABASE_URL')


# Make A Flask App
app = Flask(__name__, template_folder="templates")


# Give The User index.html If They Go To The Homepage
@app.route("/")
def index():
    return render_template("index.html")


# Shh! This is used on the back end to get information about a ticket.
@app.route("/internals/get_ticket/<id_>")
def get_ticket(id_):
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ticket_id, cast_member_name, o.order_number, ticket_number, s.showtime, on_roof, "
                        "seating_group, tickets_in_order, \"cast\" FROM tickets INNER JOIN orders o on "
                        "tickets.order_number = o.order_number INNER JOIN showtimes s on tickets.showtime = s.showtime "
                        " WHERE ticket_id=%(ticket_id)s ORDER BY tickets.order_number, ticket_number;",
                        {"ticket_id": id_})
            try:
                return Response(json.dumps(dict(cur.fetchone()), default=str), mimetype="application/json")
            except TypeError:
                return Response(status=404)


@app.route("/internals/mark_ticket_as_scanned/<id_>", methods=['PUT'])
def mark_ticket_as_scanned(id_):
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE tickets SET scanned=true WHERE ticket_id=%(ticket_id)s RETURNING ticket_id;",
                        {"ticket_id": id_})
            print(cur.fetchone())
            if cur.fetchone() is not None:
                return Response(status=204)
            else:
                return Response(status=404)


@app.route("/internals/mark_ticket_as_not_scanned/<id_>", methods=['PUT'])
def mark_ticket_as_not_scanned(id_):
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE tickets SET scanned=false WHERE ticket_id=%(ticket_id)s RETURNING ticket_id;",
                        {"ticket_id": id_})
            print(cur.fetchone())
            if cur.fetchone() is not None:
                return Response(status=204)
            else:
                return Response(status=404)


# Runs A Development Server If You Directly Run The Script
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
