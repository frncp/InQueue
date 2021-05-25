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

// TODO: Add cookie for last position


function localityModifier() {
    getPosition(getLatLonAndUpdateCityName)
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
    cityName = getCityName()
    changeCityName(cityName)
}

function getPosition(doOnSuccess) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(doOnSuccess)
    } else {
        // TODO: Input manually
    }
}

function getLatLon(position) {
    lat = position.coords.latitude
    lon = position.coords.longitude
}


function getCityName() {
    let NominatimAPI = "https://nominatim.openstreetmap.org/reverse?lat=" + lat + "&lon=" + lon + "&format=jsonv2&accept-language=it&zoom=10"

    let request = new XMLHttpRequest()
    request.open('GET', NominatimAPI, false)//false is for synchronous request

    request.onerror = function() {
        // TODO?: Add different behaviour to find a position
        console.log("Server connection error")
    };

    request.send(null)

    let data = JSON.parse(request.responseText)
    return data.name
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


