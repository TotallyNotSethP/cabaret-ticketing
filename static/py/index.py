from browser import window, document, ajax


def start_camera(cameras):
    if len(cameras) > 0:
        scanner.start(cameras[0])
    else:
        window.jQuery('#content-goes-here').html('No cameras found.')


def get_ticket(ticket_id):
    def on_complete(request):
        global content
        content = request.text
    content = ""
    ajax.get(f'/internals/get_ticket/{ticket_id}', oncomplete=on_complete)
    return content


scanner = window.Instascan.Scanner.new({"video": document.getElementById('preview'), "mirror": False})
scanner.addListener('scan', lambda content, _: window.jQuery('#content-goes-here').html(get_ticket(content)))

window.Instascan.Camera.getCameras().then(start_camera).catch(lambda e: window.jQuery('#content-goes-here').html(e))
