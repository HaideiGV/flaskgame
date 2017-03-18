/**
 * Created by slava on 3/18/17.
 */
$(document).ready(function(){
    var socket = io.connect('http://'+document.domain+':'+location.port+'/test');

    socket.on('bot connecting', function(msg) {
        $('#connecting').append('<p>'+ msg.name+' ' + msg.data+'</p>');
    });


    socket.on('bot cell response', function(msg) {
        $('#'+msg.data).append(msg.name);
        $('#'+msg.data).attr("data-status", "false");
        $('#'+msg.bot_step).append('Bot');
        $('#game-board').attr("data-bot", "true");
        $('#'+msg.bot_step).attr("data-status", "false");
    });


    socket.on('bot wins response', function(msg) {
        $('.cell').attr("data-status", "false");
        $('#log').append('<p id="wins">'+ msg.win+' Wins!</p>');
        alert(msg.win+' Wins!');
    });

    socket.on('bot response', function(msg) {
        $('#log').append('<p>Received: from '+ msg.name + ' to -> '+ msg.data + '</p>');
    });

    socket.on('server test response', function(msg) {
//        		$('#log').append('<p>Received: from '+ msg.name + ' to -> '+ msg.data + '</p>');
    });



    $('.cell').click(function(event) {
        var cell_id = $(this).attr('id');
        var bot_request = $("#game-board");
        if (bot_request.attr('data-bot') === "true"){
            if ($(this).attr('data-status') === "true"){
                $('#'+cell_id).attr("data-status", "false");
                bot_request.attr("data-bot", "false");
                socket.emit('bot cell event', {data: cell_id});
            }else{
                alert('Field is already clicked!');
            }
        }else{
            alert('Wait for bot request!');
        }
        return false;
    });

    $('.cell').click(function(event) {
        var cell_id = $(this).attr('id');
        socket.emit('bot event', {data: cell_id});
        return false;
    });

});