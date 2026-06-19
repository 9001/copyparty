// service worker. required for PWAs
// https://www.digitalapplied.com/blog/progressive-web-apps-2026-pwa-performance-guide
// Register service worker on page load
console.log('sw.js')
if ('serviceWorker' in navigator) {
    console.log('sw load')
    self.addEventListener("fetch", (event) => {
        // Regular requests not related to Web Share Target.
        if (event.request.method !== "POST" || !event.request.action.has("share-target")) {
            console.log('normal response')
            event.respondWith(fetch(event.request));
            return;
        }

        // Requests related to Web Share Target.
        event.respondWith(
            (async () => {
                const formData = await event.request.formData();
                const files = formData.get("files") || "";
                console.log('sw share:')
                console.log(files)
                await addResourcesToCache(files)

                // const responseUrl = '/'; // (ToDo: remember last upload dir)
                // ToDo: keep file references in clipboard 
                // (maybe read from cache on page load somehow)
                // -> upload on paste

                // Copy existing headers
                const headers = new Headers(event.request.headers);

                // Set a new header
                var pw = await CookieStore.get('cppwd');
                headers.set('pw', pw);
                
                headers.delete('origin'); // 99% sure this doesn't work, but hey

                const newRequest = new Request(event.request, {
                    mode: 'cors',
                    credentials: 'omit',
                    headers: headers
                })
                return fetch(newRequest)
            })(),
        );
    });
    self.addEventListener('install', (event) => {
        console.log('sw wait skip')
        self.skipWaiting(); // insta replace old service workers (helpful for dev)
    });
    const addResourcesToCache = async (resources) => {
        const cache = await caches.open("files");
        await cache.addAll(resources);
    };
}