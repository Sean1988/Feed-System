
//Initialize Redis
var _redis = require('redis');
var redis = _redis.createClient();

//Initialize  socket.io
var io = require('socket.io').listen(8070);

var data;
var user="notice:user_id:abc";
//Send message to client
io.sockets.on('connection', function(socket){

           redis.subscribe(user);
           redis.on("message",function(channel,message){
                data=message;
                console.log(message);
                socket.emit('msg',{'msg':message});
                console.log("client channel recieve from channel : %s, the message : %s", channel, message);
            });

           var redis2=_redis.createClient();
           socket.on('client_data',function(data){
                console.log("user id:"+data.userid);
                redis2.sadd("LiveUser",data.userid);
           });
});




