var since = 0;
setInterval(function() {
    fetch('/user/notifications')
        .then(response => response.json())
        .then(function(data) {
            for (var i = 0; i < data.length; i++) {
                if (data[i].name == 'unread_message_count') {
                    if (data[i].data > 0) {
                        document.getElementById("messages_unread").textContent = data[i].data;
                    } else {
                        document.getElementById("messages_unread").textContent = '';
                    }
                }
            }
        });
}, 5000);