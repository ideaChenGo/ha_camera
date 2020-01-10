const Stream = require('node-rtsp-stream')
stream = new Stream({
    name: 'name',
    streamUrl: 'rtsp://admin:123456@192.168.1.114:554/',
    wsPort: 9999,
    ffmpegOptions: { // options ffmpeg flags
        '-stats': '', // an option with no neccessary value uses a blank string
        '-r': 30 // options with required values specify the value after the key
    }
})