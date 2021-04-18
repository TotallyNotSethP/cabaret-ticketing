# Imports
import os
import json

from flask import Flask, make_response, render_template
import psycopg2

# Make A Flask App
app = Flask(__name__, template_folder="templates")


# Give The User index.html If They Go To The Homepage
@app.route("/")
def index():
    return render_template("index.html")


# Shh! This will soon be used to get information about a ticket.
@app.route("/internals/get_id/<str:id_>")
def get_id(id_):
    DATABASE_URL = os.environ.get('DATABASE_URL')
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tickets WHERE ticket_id=%(ticket_id)s;", {"ticket_id": id_})
            response = make_response(json.dumps(dict(cur.fetchone())))
    response["Content-Type"] = "application/json"
    return response


# Runs A Development Server If You Directly Run The Script
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
