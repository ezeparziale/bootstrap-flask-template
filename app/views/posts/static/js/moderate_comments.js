function disableComment(comment_id) {
    console.log(comment_id)
    fetch("./comment/disable/" + comment_id)
        .then(resource => resource.json())
        .then((data) => {
            document.getElementById(`disable-comment-${comment_id}-txt`).innerHTML = data.text;
            if (data.disable) {
                document.getElementById(`comment-${comment_id}`).innerHTML = `<span class="badge text-bg-warning">Comentario deshabilitado</span>`;
            } else {
                document.getElementById(`comment-${comment_id}`).innerHTML = data.content;
            }
        })
}