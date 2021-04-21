from browser import window, document

scanner = window.Instascan.Scanner.new({"video": document.getElementById('preview'),
                                        "mirror": False})

scanner.addListener('scan', lambda content: window.jQuery('#content-goes-here').html(content))


def startCamera(cameras):
    if len(cameras) > 0:
        scanner.start(cameras[0])
    else:
        window.jQuery('#content-goes-here').html('No cameras found.')


window.Instascan.Camera.getCameras().then(startCamera).catch(lambda e: window.jQuery('#content-goes-here').html(e))
