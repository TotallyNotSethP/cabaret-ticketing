import requests
import tempfile
import urllib

DATA = "2 Tickets For John Doe"

if __name__ == "__main__":
    response = requests.get("https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({"data": DATA}))
    print(response.content)
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".png") as f:
        f.write(response.content)
        f.seek(0)
        print(f.read())
