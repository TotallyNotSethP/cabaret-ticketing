# Imports
from flask import Flask, make_response, render_template

# Make A Flask App
app = Flask(__name__, template_folder="templates")


# Give The User index.html If They Go To The Homepage
@app.route("/")
def index():
    return render_template("index.html")


# Shh! This will soon be used to get information about a ticket.
@app.route("/internals/get_id/<int:id_>")
def get_id(id_):
    response = make_response("Not implemented yet.", 503)
    response["Content-Type"] = "text/plain"
    return response


# Runs A Development Server If You Directly Run The Script
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
