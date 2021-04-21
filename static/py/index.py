from browser import window, document, ajax
import json


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
    content = json.loads(content)
    return content.values().join("\n")


scanner = window.Instascan.Scanner.new({"video": document.getElementById('video-preview'), "mirror": False})
scanner.addListener('scan', lambda content, _: window.jQuery('#qr-code-info').html(get_ticket(content)))

window.Instascan.Camera.getCameras().then(start_camera).catch(lambda e: window.jQuery('#qr-code-info').html(e))
