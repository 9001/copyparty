// service worker. required for PWAs
// https://www.digitalapplied.com/blog/progressive-web-apps-2026-pwa-performance-guide
// Register service worker on page load
// modern syntax allowed here, only supported browsers load this file
console.log('sw load')
self.addEventListener("fetch", (event) => {
    // Regular requests not related to Web Share Target.
    console.log(event.request.url)
    var [baseurl, query] = event.request.url.split('?');
    if (event.request.method !== "POST" || !query.match("share-target")) {
        var toplevel = baseurl == self.location.origin;
        if(query?.match("PWA") && toplevel){
            // prevent cors restriction
            event.respondWith(
                fetch(new Request("/", { mode: 'same-origin' }))
            );
        }
        return;
    }

    // Requests related to Web Share Target.
    event.respondWith(
        (async () => {
            try{
                const formData = await event.request.formData();
                const files = formData.getAll('media');

                // store in cache for retrieval in up2k.js.
                const cache = await caches.open('/media');
                for(var i = 0; i < files.length; i++){
                    console.log("caching file" + i)
                    await cache.put('/shared-file-' + i, new Response(files[i]))
                    await cache.put('/shared-filename-' + i, new Response(files[i].name))
                }

                await cache.put('/shared-file-count', new Response(files.length))

                return Response.redirect('/?share-target', 303);
            }
            catch(e){
                console.log(e)
            }
        })(),
    );
});
self.addEventListener('install', () => {
    console.log('sw wait skip')
    self.skipWaiting(); // insta replace old service workers (helpful for dev)
});