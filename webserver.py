# Imports
import os
import json

import flask
from flask import Flask, Response, render_template
import psycopg2
import psycopg2.extras

# Make A Flask App
app = Flask(__name__, template_folder="templates")


# Give The User index.html If They Go To The Homepage
@app.route("/")
def index():
    return render_template("index.html")


# Shh! This will soon be used to get information about a ticket.
@app.route("/internals/get_ticket/<id_>")
def get_ticket(id_):
    DATABASE_URL = os.environ.get('DATABASE_URL')
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ticket_id, cast_member_name, o.order_number, ticket_number, s.showtime, on_roof, "
                        "seating_group, tickets_in_order, \"cast\" FROM tickets INNER JOIN orders o on "
                        "tickets.order_number = o.order_number INNER JOIN showtimes s on tickets.showtime = s.showtime "
                        " WHERE ticket_id=%(ticket_id)s ORDER BY tickets.order_number, ticket_number;",
                        {"ticket_id": id_})
            return flask.Response(json.dumps(dict(cur.fetchone()), default=str), mimetype="application/json")


# Runs A Development Server If You Directly Run The Script
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
