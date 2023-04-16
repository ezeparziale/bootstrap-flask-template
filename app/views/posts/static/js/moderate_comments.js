function disableComment(comment_id) {
    console.log(comment_id)
    fetch("./comment/disable/" + comment_id)
        .then(resource => resource.json())
        .then((data) => {
            document.getElementById(`disable-comment-${comment_id}-txt`).innerHTML = data.text;
           
        })
}