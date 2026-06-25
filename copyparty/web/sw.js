// service worker. required for PWAs
// https://www.digitalapplied.com/blog/progressive-web-apps-2026-pwa-performance-guide
// Register service worker on page load
// modern syntax allowed here, only supported browsers load this file
console.log('sw load')
self.addEventListener("fetch", (event) => {
    // Regular requests not related to Web Share Target.
    var [baseurl, query] = event.request.url.split('?');
    var isCrossSiteInit = !event.clientId && event.request.mode === 'navigate';
    if (event.request.method !== "POST" || !query.match("share-target")) {
        if(query.match("utm_source=launcher") || isCrossSiteInit){
            // prevent cors restriction
            event.respondWith(
                fetch(new Request(self.location.origin, { mode: 'same-origin' }))
            );
            return;
        }
        console.log('normal response')
        event.respondWith(fetch(event.request));
        return;
    }

    // Requests related to Web Share Target.
    event.respondWith(
        (async () => {
            try{
                const formData = await event.request.formData();
                const files = formData.getAll('files');

                // store in cache for retrieval in up2k.js.
                // leading "/" is necessary, because cache 
                // operates relative to path of current file
                const cache = await caches.open('/media');
                for(var i = 0; i < files.length; i++){
                    await cache.put('/shared-file-' + i, new Response(files[i]))
                    await cache.put('/shared-filename-' + i, new Response(files[i].name))
                }

                await cache.put('/shared-file-count', new Response(files.length))

                return Response.redirect('/?share-target', 303);
            }
            catch(e){
                alert(e)
            }
        })(),
    );
});
self.addEventListener('install', (event) => {
    console.log('sw wait skip')
    self.skipWaiting(); // insta replace old service workers (helpful for dev)
});