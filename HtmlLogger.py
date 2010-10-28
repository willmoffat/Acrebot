#! /usr/bin/env python

#from IPython.Shell import IPShellEmbed
import time
import logging
import cgi
import re
import os
from logging.handlers import TimedRotatingFileHandler


class TimedRotatingHtmlFileHandler(TimedRotatingFileHandler):
    """Rotating file handler that starts with <html> and ends with </html>"""
    
    ACRE_SCRIPT = 'http://acrebot.freebaseapps.com'
    
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None):
        print 'Html log: start'
        TimedRotatingFileHandler.__init__(self, filename, when, interval, backupCount, encoding)
        self.header()
    
    def close(self):
        print 'Html log: stop'
        self.footer()
        TimedRotatingFileHandler.close(self)
    
    def doRollover(self):
        print 'Html log: rollover'
        
        # Calculate the new name of this file using the same code as superclass:
        # /Library/Frameworks/Python.framework/Versions/2.5/lib/python2.5/logging/handlers.py
        t = self.rolloverAt - self.interval
        timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        
        self.footer()
        TimedRotatingFileHandler.doRollover(self)
        rotated_filename =  os.path.basename(dfn)
        self.header(rotated_filename)
    
    def header(self,previous_file=None):
        title = 'Acrebot log: '+ time.asctime()
        html = ''
        html += '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n'
        html += '<html><head>\n'
        html += '  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" >\n'
        html += '  <link rel="stylesheet" type="text/css" href="'+self.ACRE_SCRIPT+'/logs-css">\n'
        html += '  <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.1/jquery.min.js"></script>\n'
        html += '  <script type="text/javascript" src="'+self.ACRE_SCRIPT+'/logs-js"></script>\n'        
        html += '  <title>' + title + '</title>\n</head>\n'
        html += '<body><h1>'+title+'</h1>\n'
        if previous_file:
            html += '  <div class="prev"><a href="'+previous_file+'">Previous</a> file</div>\n'
        self.stream.write(html)
        
    def footer(self):
        html = '<div class="end">End of file</div>\n</body></html>'
        self.stream.write(html)
    


class HtmlLogger():
    def __init__(self,channel_name='#testwill1'):
        channel  = channel_name[1:]     # strip the hash symbol off 
        dirname  = 'output/'+channel
        filename = dirname + '/' + channel+'.html'
        try:
            os.makedirs(dirname)
        except OSError:
            # dir already existed
            pass
        
        # Set up a specific logger with our desired output level
        self.logger = logging.getLogger(channel) # we use channel as a unqiue label for this logger
        self.logger.setLevel(logging.DEBUG)
        
        # Add the log message handler to the logger
        # Rotate at midnight
        handler = TimedRotatingHtmlFileHandler(filename, when='midnight')
        
        # HTML Formatting
        formatter = logging.Formatter("<div%(irc_class)s><i>%(asctime)s</i><s>%(irc_user)s</s><b>%(message)s</b></div>","%H:%M:%S")
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def event(self,nick,msg,typ=''):
        nick = cgi.escape(nick)
        msg  = cgi.escape(msg)
        typ  = cgi.escape(typ)
        # remove trailing _ from nick when creating class
        userclass = ' user-' + re.sub('_+$','',nick)
        irc_class = ' class="'+typ+userclass+'"'
        self.logger.info(msg, extra={'irc_user':nick, 'irc_class':irc_class})
    



if __name__ == '__main__':
    print "Starting tests"
    (IRC_NICK,IRC_CHANNELS) = ("acrebot2" , ["#testwill1","#testwill2"])
    loggers = {}
    for channel in IRC_CHANNELS:
        loggers[channel] = HtmlLogger(channel_name=channel)
        
    l = loggers["#testwill1"]
    l.event('will','-----------test message-----------','class')

    # Force a rollover
    #ipshell = IPShellEmbed(); ipshell()
    #l.logger.handlers[0].doRollover()
    
    print "Finished"




