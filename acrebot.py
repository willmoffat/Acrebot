#! /usr/bin/env python

import sys
import re
import os
import urllib2
import string

from irclib import SimpleIRCClient
from HtmlLogger import HtmlLogger
import webserver

#from IPython.Shell import IPShellEmbed
#ipshell = IPShellEmbed(); ipshell()

# limits for msgs sent by bot
MAX_LEN      = 400
MAX_LINES    = 5

IRC_SERVER   = "irc.freenode.net"
IRC_PORT     = 6667
IRC_NICK     = "acrebot"  # probably best if you choose a new name
IRC_PASS     = "REDACTED" # and register a new password on freenode
IRC_CHANNELS = ["#grefine","#freebase"]

ACREBOT_OTG_SCRIPT     = 'http://acrebot.willmoffat.user.dev.freebaseapps.com'
ACREBOT_SANDBOX_SCRIPT = 'http://acrebot.willmoffat.user.dev.sandbox-freebaseapps.com'

# TODO: check IRC_NICK == conn.get_nickname()


class AcreBot(SimpleIRCClient, object):
    def __init__(self):
        super(AcreBot, self).__init__()
        self.loggers = {}

    def do_log(self,event):
        nick = self.short_nick(event)
        typ  = string.upper(event.eventtype())
        msg  = " ".join(event.arguments())
        if event.target():
            channels = [event.target()]
        else:
            channels = IRC_CHANNELS   # events like QUIT don't have a target, HACK: send them to all channels
        for channel in channels:
            logger = self.loggers[channel.lower()]
            logger.event(nick,msg,typ)
        
    
    def do_notice(self,msg,original_event):
        ''' notice is for messages that should _never_ be responded to (like acrebot output)
            there is no on_notice - this is probably good, since I can't get into any kind of loop - but should I log it?
            If original_event is not set, then log to stdout for testing'''
        output = self.irc_quote(msg)
        if not original_event:
            print '-->'+msg
            return
        target = original_event.target()
        if (target[0]=='#'):
            logger = self.loggers[target.lower()]
            logger.event(IRC_NICK,output,'ACREBOT')
        else:
            target = self.short_nick(original_event)
        self.connection.notice(target,output)
    
    def do_notice_on_channel(self,output,channel):
        if not channel in IRC_CHANNELS:
            return "Error: invalid channel. List: " + ", ".join(IRC_CHANNELS) + "\n"
        self.loggers[channel.lower()].event('invalidusername',output, 'BROADCAST')
        self.connection.notice(channel,output)
        return "Msg sent OK\n"
    
    def do_notice_all_channels(self,output):
        for channel in IRC_CHANNELS:
            self.do_notice_on_channel(output,channel)
    
    def irc_quote(self,str):
        if str[0]=='/':
            str = '/'+str  # quote /commands
        str = str.encode('string_escape') # make sure we have no controls chars - TODO: this probably kills unicode as well
        str = str.replace("\\'","'")      # ' is OK
        return str;
    
    def truncate_result(self,result):
        snipped_chars = len(result)-MAX_LEN
        result        = result[0:MAX_LEN]
        lines         = result.splitlines()
        snipped_lines = len(lines)-MAX_LINES
        lines         = lines[0:MAX_LINES]
        trunc = ''
        if snipped_chars>0:
            trunc =  ' + '+str(snipped_chars)+' chars.'
        elif snipped_lines>0:
            trunc = ' + '+str(snipped_lines)+ ' lines.'
        if trunc:
            lines.append(trunc)
        return lines
    
    def short_nick(self, event):
        '''hide the real username and IP'''
        return event.source().split('!')[0]
    
    def eval_cmd(self,url):
        #print 'DEBUG: '+url+'\n'
        try:
            response = urllib2.urlopen(url)
            result = response.read()
        except:
            (ty,v,tr)=sys.exc_info()
            result = str(v)
        lines = self.truncate_result(result)
        return lines
    
    def stop_bot(self,event):
        killer = event.source() # use full username and ip
        output = 'Terminated by '+killer
        self.do_notice_all_channels(output)
        raise SystemExit("Bot terminated")
    
    def handle_command(self,event, msg_override=None):
        msg = msg_override or " ".join(event.arguments())
        
        # Log if testing
        if not event: print '>'+msg
        
        # support JIRA command (even without acrebot: in msg)
        regexp = re.compile(r'\b((ACRE|APPS|CACHE|CDB|CLI|GD|LOG|ME|ENG|MQL|MWBUILD|REL|TEST|DOC|FREEBASE|TOOL|IQ)-\d+)\b')
        r = re.search(regexp,msg)
        if r:
            msg = IRC_NICK+': '+r.group(0)

        # Make sure acrebot: is in msg
        r = re.search('^'+IRC_NICK+':?\s*(s-)?',msg)
        if not r: return False
        
        cmd = msg[r.end():]

        if cmd == 'DIE': self.stop_bot(event)

        if r.group(1):
            script = ACREBOT_SANDBOX_SCRIPT
        else:
            script = ACREBOT_OTG_SCRIPT

        # send the rest of the line to AcreBot JS
        cmd = urllib2.quote(cmd)
        url = script+'/do?msg='+cmd;
        lines = self.eval_cmd(url)
        for line in lines:
            self.do_notice(line,event)
        return True
    
    def on_welcome(self, conn, event):
        self.connection.privmsg('nickserv', 'identify '+IRC_PASS)
        for channel in IRC_CHANNELS:
            self.loggers[channel.lower()] = HtmlLogger(channel_name=channel)
            self.connection.join(channel)
        
    
    def on_privmsg(self, conn, event): # private message to acrebot
        # not logged
        self.handle_command(event)
    
    def on_action(self, conn, event): # /me
        self.do_log(event)
    
    def on_join(self, conn, event): # /join
        self.do_log(event)
    
    def on_part(self, conn, event): # /leave
        self.do_log(event)
    
    def on_pubmsg(self, conn, event): # normal message
        self.do_log(event)
        self.handle_command(event)
    
    def on_quit(self, conn, event): # /quit
        self.do_log(event)
    
    # def on_mode(self, conn, event):
    #     nick = event.source().split('!')[0]
    #     self.log.event(nick, "-MODE- set mode %s" % (' '.join(event.arguments())))
    # 
    # def on_kick(self, conn, event):
    #     nick = event.source().split('!')[0]
    #     target = event.target().split('!')[0]
    #     self.log.event(nick, "-KICK- kicked %s (%s)" % (target, ' '.join(event.arguments())))
    # 
    # def on_topic(self, conn, event):
    #     nick = event.source().split('!')[0]
    #     topic = ' '.join(event.arguments())
    #     self.log.event(nick, "-TOPIC- set topic to %s" % (topic))
    # 
    # 
    

if True:
    acrebot = AcreBot()
    acrebot.connect(IRC_SERVER, IRC_PORT, IRC_NICK)
    webserver.HttpServerThread( acrebot ).start()
    acrebot.start()
else:
    # run local tests
    acrebot = AcreBot()
    inputs = [
    ' ACRE-123 ',
    'ACRE-123',
    'hi',
    IRC_NICK+': hi',
    IRC_NICK+': s-eval(acre.version)'
    ]
    for test in inputs:
        acrebot.handle_command(None,test)
        print

    #print acrebot.eval_cmd('http://acrebot.willmoffat.user.dev.sandbox-freebaseapps.com/do?msg=eval%28while%281%29%7B%7D%29')
    #log = HtmlLogger()
    #log.event('willmoffat','hello world','TESTCLASS')
    #log.event('willmoffat','without class')

