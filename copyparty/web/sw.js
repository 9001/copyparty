// service worker. required for PWAs
// https://www.digitalapplied.com/blog/progressive-web-apps-2026-pwa-performance-guide
// Register service worker on page load
if ('serviceWorker' in navigator) {
    self.addEventListener("fetch", (event) => {
        // Regular requests not related to Web Share Target.
        if (event.request.method !== "POST" || !event.request.enctype.has("share-target")) {
            event.respondWith(fetch(event.request));
            return;
        }

        // Requests related to Web Share Target.
        event.respondWith(
            (async () => {
            const formData = await event.request.formData();
            const link = formData.get("link") || "";
            // Instead of the original URL `/save-bookmark/`, redirect
            // the user to a URL returned by the `saveBookmark()`
            // function, for example, `/`.
            const responseUrl = await saveBookmark(link);
            return Response.redirect(responseUrl, 303);
            })(),
        );
    });
    window.addEventListener('load', async () => {
        try {
            const registration = await navigator.serviceWorker.register(
                '/service-worker.js',
                { scope: '/' }
            );
            console.log('SW registered:', registration.scope);

            // Check for waiting update
            if (registration.waiting) {
                notifyUserOfUpdate(registration);
            }

            // Listen for future updates
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                newWorker?.addEventListener('statechange', () => {
                if (
                    newWorker.state === 'installed' &&
                    navigator.serviceWorker.controller
                ) {
                    notifyUserOfUpdate(registration);
                }
            });
        });
        } catch (error) {
            console.error('SW registration failed:', error);
        }
    });
}