from browser import window, document, ajax, timer
import json
import datetime
import re


class PST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-8)

    def tzname(self, dt):
        return "PST"

    def dst(self, dt):
        return datetime.timedelta(hours=-7)


def start_camera(cameras):
    if len(cameras) > 0:
        camera_param = window.URLSearchParams.new(window.location.search).get("camera")
        if camera_param:
            scanner.start(cameras[int(camera_param)])
        else:
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
    showtime = datetime.datetime.fromisoformat(str(content["showtime"])).replace(tzinfo=PST())
    print(showtime - datetime.timedelta(hours=1), showtime, datetime.datetime.now(PST()), showtime + datetime.timedelta(hours=1))
    if showtime - datetime.timedelta(hours=1) <= datetime.datetime.now(PST()) <= showtime + datetime.timedelta(hours=1):
        window.jQuery("body").css("background-color", "green")
    else:
        window.jQuery("body").css("background-color", "red")
    return "<br>".join([
        "Name: " + str(content["cast_member_name"]),
        "Showtime: " + re.sub(r"^0|(?<=\s)0", "", re.sub(r"(?<=[0-9])[AP]M", lambda m: m.group().lower(),
                                                         showtime.strftime("%a %m/%d/%y %I%p")))
        + (" (Roof)" if content["on_roof"] else "")
    ])


scanner = window.Instascan.Scanner.new({"video": document.getElementById('video-preview'), "mirror": False})
scanner.addListener('scan', lambda content, _: window.jQuery('#qr-code-info').html(get_ticket(content)))

window.Instascan.Camera.getCameras().then(start_camera).catch(lambda e: window.jQuery('#qr-code-info').html(e))
