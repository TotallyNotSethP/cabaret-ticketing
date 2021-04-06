import requests
import urllib

if __name__ == "__main__":
    DATA = "2 Tickets For John Doe"

    response = requests.get("https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({"data": DATA}))

    with open("qrcode.png", "wb") as f:
        f.write(response.content)
