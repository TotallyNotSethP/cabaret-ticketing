from browser import window, document, ajax, timer, html
import json
import datetime
import re


class PST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-7)

    def tzname(self, dt):
        return "PST"

    def dst(self, dt):
        return datetime.timedelta(hours=-7)


def start_camera(cameras):
    if len(cameras) > 0:
        for i, camera in enumerate(cameras):
            document.getElementById("camera-picker") <= html.OPTION(camera.name, **{"value": camera.id,
                                                                                    "id": "cam-" + camera.id,
                                                                                    "class": "first-camera"
                                                                                    if i == 0 else ""})
        camera_param = window.URLSearchParams.new(window.location.search).get("camera")
        if camera_param:
            for camera in cameras:
                if camera.id == camera_param:
                    scanner.start(camera)
                    document.getElementById("cam-" + camera_param).selected = True
                    break
            else:
                window.jQuery('#qr-code-info').html(f'Camera with ID \'{camera_param}\' not found.')
        else:
            scanner.start(cameras[0])
            document.getElementsByClassName("first-camera")[0].selected = True
            window.jQuery('#camera-picker').hideOption('cam-placeholder')
    else:
        window.jQuery('#qr-code-info').html('No cameras found.')


def get_ticket(ticket_id):
    def on_complete(request):
        global content, status
        print(request.status)
        content = request.text
        status = request.status

    ajax.get(f'/internals/get_ticket/{ticket_id}', oncomplete=on_complete, blocking=True)

    def get_content():
        global content
        try:
            if content[0] == "{":
                content = json.loads(content)
            else:
                content = ""
        except UnboundLocalError:
            timer.setTimeout(get_content, 100)
        except SyntaxError:
            content = ""

    get_content()
    if status == 200:
        showtime = datetime.datetime.fromisoformat(str(content["showtime"])).replace(tzinfo=PST())
        print(showtime - datetime.timedelta(hours=1), showtime, datetime.datetime.now(PST()), showtime + datetime.timedelta(hours=1))
        if not showtime - datetime.timedelta(hours=1) <= datetime.datetime.now(PST()) <= showtime + datetime.timedelta(hours=1):
            window.jQuery("body").css("background-color", "red")
            window.jQuery("#warnings-and-errors").html("WRONG SHOWTIME")
            return ""
        elif bool(content["scanned"]):
            window.jQuery("body").css("background-color", "red")
            window.jQuery("#warnings-and-errors").html("ALREADY BEEN SCANNED")
            return ""
        else:
            window.jQuery("body").css("background-color", "green")
            window.jQuery("#warnings-and-errors").html("")
            req = ajax.Ajax()
            req.open("PUT", f"/internals/mark_ticket_as_scanned/{ticket_id}")
            req.send()
            return "<br>".join([
                "Name: " + str(content["cast_member_name"]),
                "Showtime: " + re.sub(r"^0|(?<=\s)0", "", re.sub(r"(?<=[0-9])[AP]M", lambda m: m.group().lower(),
                                                                 showtime.strftime("%a %m/%d/%y %I%p")))
                + (" (Roof)" if content["on_roof"] else ""),
                "Ticket Number: " + str(content["ticket_number"])
            ])
    else:
        window.jQuery("body").css("background-color", "red")
        window.jQuery("#warnings-and-errors").html("UNKNOWN TICKET ID")
        return ""


def change_camera(this):
    window.location.replace(
        f"https://jr-musical-theater-ticketing.herokuapp.com/?camera={document.getElementById('camera-picker').value}")


document.getElementById('camera-picker').onchange = change_camera

scanner = window.Instascan.Scanner.new({"video": document.getElementById('video-preview'), "mirror": False})
scanner.addListener('scan', lambda content, _: window.jQuery('#qr-code-info').html(get_ticket(content)))

window.Instascan.Camera.getCameras().then(start_camera).catch(lambda e: window.jQuery('#qr-code-info').html(e))
