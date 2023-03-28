function reset_avatar() {
    fetch("./reset_avatar")
        .then(resource => resource.json())
        .then((data) => {
            document.getElementById(`avatar`).src = data.image_file;
        })
}