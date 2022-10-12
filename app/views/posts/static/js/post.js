function likePost(post_id){
    fetch("./like_post/" + post_id)
    .then(resource => resource.json())
    .then((data) => {
        document.getElementById("likes-counts").innerHTML = data.likes;
        document.getElementById("likes-icon").classList.value = data.icon;
    })
}

function favoritePost(post_id){
    fetch("./favorite_post/" + post_id)
    .then(resource => resource.json())
    .then((data) => {
        document.getElementById("favs-icon").classList.value = data.icon;
    })
}


function reportPost(post_id){
    fetch("./report_post/" + post_id)
    .then(resource => resource.json())
    .then((data) => {
        document.getElementById("report-post-icon").classList.value = data.icon;
    })
}



function likeComment(comment_id){
    fetch("./like_comment/" + comment_id)
    .then(resource => resource.json())
    .then((data) => {
        document.getElementById(`likes-comment-${comment_id}-counts`).innerHTML = data.likes;
        document.getElementById(`likes-comment-${comment_id}-icon`).classList.value = data.icon;
    })
}


function reportComment(comment_id){
    fetch("./report_comment/" + comment_id)
    .then(resource => resource.json())
    .then((data) => {
        document.getElementById(`report-comment-${comment_id}-icon`).classList.value = data.icon;
    })
}


function disableComment(comment_id){
    fetch("./moderate/comment/disable/" + comment_id)
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