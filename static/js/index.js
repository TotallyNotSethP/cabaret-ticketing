var audio = false;
var error_sound = new Audio("static/mp3/error.mp3");
var valid_sound = new Audio("static/mp3/valid.mp3");

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

$(document).ready(function() {
  let scanner = new Instascan.Scanner({video: document.getElementById('video-preview'), mirror: false}); // Scanner Preview @ #video-preview
  scanner.addListener('scan', function (content) { // When QR Code scanned...
    fetch("/internals/get_ticket/" + content) // Get the ticket matching the id
      .then(response => response.json()) // Convert the received ticket info to object
      .then(async data => {
        $("body").css("background-color", "white"); // Quickly flash white
        await sleep(250);
        $("body").css("background-color", data["color"]); // Then turn the specified color
        $("#errors").html(data["error"]); // Display any errors
        $("#qr-code-info").html(data["ticket_info"]); // Display ticket info
        if (audio) {
          if (data["sound"] === "error") await error_sound.play();
          else await error_sound.play();
        }
      })
  });
  Instascan.Camera.getCameras().then(function (cameras) { // Get a list of available cameras
    if (cameras.length > 0) { // If there are any cameras...
      for (let i = 0; i < cameras.length; i++) {
        let cam_id = cameras[i].id;
        if (i === 0) {
          $("#camera-picker").append(`<option value="${cam_id}" id="cam-${cam_id}" class="first-camera">${cameras[i].name}</option>`); // Put them in the dropdown menu
        } else {
          $("#camera-picker").append(`<option value="${cam_id}" id="cam-${cam_id}">${cameras[i].name}</option>`);
        }
      }
      let camera_param = new URL(window.location.href).searchParams.get("camera") // See if the user has already selected a camera
      if (camera_param) { // If so...
        let camera_found = false;
        for (let i = 0; i < cameras.length; i++) {
          if (cameras[i].id === camera_param) { // See if we have a matching camera
            scanner.start(cameras[i]); // If so then start the scanner with that camera
            document.getElementById("cam-" + camera_param).selected = true;
            camera_found = true;
            break;
          }
        }
        if (!camera_found) { // If we dont have a matching camera...
          $("#qr-code-info").html(`Camera with ID '${camera_param}' not found.`); // Let the user know
        }
      } else {
        scanner.start(cameras[0]);
        let firstcam = document.getElementsByClassName("first-camera");
        firstcam[0].selected = true;
        $(`#cam-placeholder`).html("");
      }
    } else {
      $("#qr-code-info").html('No cameras found.');
    }
  }).catch(function (e) {
    $("#qr-code-info").html(e);
  });
  document.getElementById('camera-picker').onchange = () => {
     window.location.replace(`https://${window.location.hostname}/?camera=${document.getElementById('camera-picker').value}`)
  }
});

const button = document.querySelector("#enable-audio");
button.addEventListener('click', event => {
  button.textContent = "";
  audio = true;
});
