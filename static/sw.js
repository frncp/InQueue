let cacheName = 'pwa_2021';
let filesToCache = [ //Commented out because of pages not refreshing
//    'static/css/style.css',
//    'static/js/main.js',
    'static/css/bootstrap.css',
    'static/css/leaflet.css',
    'static/js/leaflet.js',
    'static/js/jquery.js',
    'static/images/waiter.png',
    'static/images/soccer-field.png',
    'static/images/OOjs_UI_icon_upload.svg.png',
    'static/images/museum.png',
    'static/images/nail-polish.png',
    'static/images/muscle.png',
    'static/images/mechanic.png',
    'static/images/lawyer.png',
    'static/images/barbershop.jpg',
    'static/images/barber.png'
];


/* Start the service worker and cache all of the app's content */
self.addEventListener('install', function(e) {
    e.waitUntil(
        caches.open(cacheName).then(function(cache) {
            return cache.addAll(filesToCache);
        })
    );
});

/* Serve cached content when offline */
self.addEventListener('fetch', function(e) {
    e.respondWith(
        caches.match(e.request).then(function(response) {
            return response || fetch(e.request);
        })
    );
});