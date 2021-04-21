from browser import window, document, ajax, timer
import json
import datetime
import re


def start_camera(cameras):
    if len(cameras) > 0:
        scanner.start(cameras[0])
    else:
        window.jQuery('#qr-code-info').html('No cameras found.')


def get_ticket(ticket_id):
    def on_complete(request):
        global content
        content = request.text

    ajax.get(f'/internals/get_ticket/{ticket_id}', oncomplete=on_complete, blocking=True)

    def get_content():
        global content
        try:
            content = json.loads(content)
        except UnboundLocalError:
            timer.setTimeout(get_content, 100)

    get_content()
    return "<br>".join([
        "Name: " + str(content["cast_member_name"]),
        "Order Number: " + str(content["order_number"]),
        "Showtime: " + re.sub(r"^0|(?<=\s)0", "", re.sub(r"(?<=[0-9])[AP]M", lambda m: m.group().lower(),
                                                         datetime.fromisoformat(str(content["showtime"])).strftime(
                                                             "%a %D %I%p")))
        + (" (Roof)" if content["on_roof"] else "")
    ])


scanner = window.Instascan.Scanner.new({"video": document.getElementById('video-preview'), "mirror": False})
scanner.addListener('scan', lambda content, _: window.jQuery('#qr-code-info').html(get_ticket(content)))

window.Instascan.Camera.getCameras().then(start_camera).catch(lambda e: window.jQuery('#qr-code-info').html(e))
