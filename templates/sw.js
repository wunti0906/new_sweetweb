self.addEventListener('push', function(event) {
    const data = event.data ? event.data.json() : { title: "王國通知", body: "你的王國有新消息！" };
    
    const opts = {
        body: data.body,
        icon: 'https://cdn-icons-png.flaticon.com/512/3655/3655113.png',
        badge: 'https://cdn-icons-png.flaticon.com/512/3655/3655113.png'
    };

    event.waitUntil(
        self.registration.showNotification(data.title, opts)
    );
});

// 點擊通知打開 App
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/')
    );
});