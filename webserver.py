#! /usr/bin/env python

#TODO: support GET channel topic?
#TODO: clean shutdown? #    server.socket.close()

PORT_NUM = 7176

import SimpleHTTPServer, BaseHTTPServer
import cgi
import threading

# from IPython.Shell import IPShellEmbed
#                 ipshell = IPShellEmbed(); ipshell()
            
class MyHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def _headers(self,status):
        self.send_response(status)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
    
    def do_POST(self):
        self._headers(200)
        
        # Write out any POST data
        if self.headers.dict.has_key("content-length"):
            content_length = int(self.headers.dict["content-length"])
            raw_post_data = self.rfile.read(content_length)
            q = cgi.parse_qs(raw_post_data)
            channel = '#metaweb'
            if q.has_key('channel'):
                channel = q['channel'][0]
            if q.has_key('msg'):
                msg = q['msg'][0]
                self.wfile.write( 'RECEIVED MSG:'+msg+' for channel '+channel+'\n' )
                if hasattr(self,'logbot'):
                    response = self.logbot.do_notice_on_channel(msg,channel)
                    self.wfile.write(response)
    
    def do_GET(self):
        self._headers(404)
        self.wfile.write( 'You can only post to acrebot' )
    



class HttpServerThread ( threading.Thread ):
    def __init__(self,logbot):
        super(HttpServerThread, self).__init__()
        MyHTTPHandler.logbot = logbot;
    
    def run ( self ):
        server = BaseHTTPServer.HTTPServer(('', PORT_NUM), MyHTTPHandler)
        print 'started httpserver... on port '+str(PORT_NUM)
        server.serve_forever()
    


if __name__ == '__main__':
    class LogBot:
        def do_notice(self,msg):
            print 'TEST: '+msg
    
    HttpServerThread(LogBot()).start()

    


