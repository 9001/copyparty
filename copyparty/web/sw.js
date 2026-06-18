// service worker. required for PWAs
// https://www.digitalapplied.com/blog/progressive-web-apps-2026-pwa-performance-guide
// Register service worker on page load
if ('serviceWorker' in navigator) {
    self.addEventListener("fetch", (event) => {
        // Regular requests not related to Web Share Target.
        if (event.request.method !== "POST" || !event.request.action.has("share-target")) {
            event.respondWith(fetch(event.request));
            return;
        }

        // Requests related to Web Share Target.
        event.respondWith(
            (async () => {
            const formData = await event.request.formData();
            const files = formData.get("files") || "";
            const responseUrl = '/'; // (ToDo: remember last upload dir)
            // ToDo: keep file references in clipboard
            // -> upload on paste
            event.respondWith(fetch(event.request));
            alert(files);
            return;
            })(),
        );
    });
}