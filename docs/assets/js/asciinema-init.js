function asciinema_create_player(src, element, options) {
    //console.log('asccinema_create_player', { src, element, options })
    if (window.AsciinemaPlayer) {
        AsciinemaPlayer.create(src, element, options);
    }
}