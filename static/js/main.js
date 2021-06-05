let lat;
let lon;
let cityName;

window.onload = () => {
    'use strict'

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker
            .register('../sw.js').then(function (registration) {

                // Service worker registered correctly
                console.log('ServiceWorker registration successful with scope: ', registration.scope)
            },
            function (err) {

                // Troubles in registering the service worker
                console.log('ServiceWorker registration failed: ', err)
            });
    }
}

function localityModifier() {
    getPosition(getLatLonAndUpdateCityName, redirectToSelect, redirectToSelect)
}

function redirectToSelect() {
    window.location.href = "/select"
}

function getLatLonAndUpdateCityName(position) {
    addSpinner('selectedCity')
    let oldPos = lat+lon
    getLatLon(position)
    if (oldPos != lat+lon)
        updateCityNameByLatLon()
    else 
        changeCityName(cityName);
}

function updateCityNameByLatLon() {
    cityName = getCityName(getNominatimData(lat, lon))
    changeCityName(cityName)
    document.cookie = "city=" + cityName; 
}

function GPSInput(){
    getPosition(getLatLonAndAddToInput)
}

function getLatLonAndAddToInput(position) {
    let oldPos = lat+lon
    getLatLon(position)
    if (oldPos != lat+lon) {
        cityName = getCityName()
        document.getElementById('city').value = cityName
    }
}

function getPosition(doOnSuccess, doOnFailure, doifNotSupported) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(doOnSuccess, doOnFailure)
    } else {
        if (doifNotSupported)
        doifNotSupported()
    }
}

function getLatLon(position) {
    lat = position.coords.latitude
    lon = position.coords.longitude
}

function getNominatimData(lat, lon) {
    let NominatimAPI = "https://nominatim.openstreetmap.org/reverse?lat=" + lat + "&lon=" + lon + "&format=jsonv2&accept-language=it&zoom=18"

    let request = new XMLHttpRequest()
    request.open('GET', NominatimAPI, false)//false is for synchronous request

    request.onerror = function() {
        // TODO?: Add different behaviour to find a position
        console.log("Server connection error")
    };

    request.send(null)

    return data = JSON.parse(request.responseText)

}


function searchNominatimData(query) {
    if (query.length == 0)
        return
    let NominatimAPI = "https://nominatim.openstreetmap.org/search?q=" + query.toString() +"&format=jsonv2&accept-language=it&addressdetails=1"
    console.log(NominatimAPI)
    let request = new XMLHttpRequest()
    request.open('GET', NominatimAPI, false)//false is for synchronous request

    request.onerror = function() {
        // TODO?: Add different behaviour to find a position
        console.log("Server connection error")
    };

    request.send(null)

    return data = JSON.parse(request.responseText)

}

function getCityName(data) {
    if (typeof data.address == "undefined")
        return ""
    if (typeof data.address.city != "undefined")
        return data.address.city
    else if (typeof data.address.village != "undefined")
        return data.address.village
    else if (typeof data.address.town != "undefined")
        return data.address.town
}

function getCityRoad(data) {
    if(typeof data.address == "undefined")
        return ""
    if (typeof data.address.road != "undefined")
        return data.address.road
}

function changeCityName(cityName) {
    changeHTMLById('selectedCity', cityName)
}

function changeHTMLById(id, content) {
     let element = document.getElementById(id)
     element.innerText = content
}

function addSpinner(id) {
     let element = document.getElementById(id)
     let spinner = document.createElement('span')
     spinner.innerHTML += '<div class="spinner-border ml-5" role="status"></div>' 
     element.appendChild(spinner)
}


/* FORMS */
function showNextForm(toID, buttonID, checkFunction)  {
    if (checkFunction()) {
        removeValidateCSS()
        let toElement = document.getElementById(toID)
        toElement.classList.remove('d-none')
        window.location.replace("#"+toID)
        let button = document.getElementById(buttonID.id)
        button.classList.add('d-none')
        button.parentNode.appendChild(document.createElement("hr")).classList.add('mt-5')
    }
}

function addValidateCSS() {
    document.getElementById('form').classList.add('was-validated')
}

function removeValidateCSS() {
    document.getElementById('form').classList.remove('was-validated')
}
