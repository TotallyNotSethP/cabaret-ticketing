# Imports
from flask import Flask

# Make A Flask App
app = Flask(__name__)


# Give The User index.html If They Go To The Homepage
@app.route("/")
def index():
    with open("index.html") as f:
        return f.read()


# Shh! This will soon be used to get information about a ticket.
@app.route("/internals/getid/<int:id>")
def _get_id(id):
    pass


# Runs A Development Server If You Directly Run The Script
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
