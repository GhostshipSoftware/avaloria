"""
This module implements the telnet protocol.

This depends on a generic session module that implements
the actual login procedure of the game, tracks
sessions etc.

"""

import re
from twisted.conch.telnet import Telnet, StatefulTelnetProtocol, IAC, LINEMODE, GA, WILL, WONT, ECHO
from src.server.session import Session
from src.server.portal import ttype, mssp, msdp, naws
from src.server.portal.mccp import Mccp, mccp_compress, MCCP
from src.utils import utils, ansi, logger

_RE_N = re.compile(r"\{n$")


class TelnetProtocol(Telnet, StatefulTelnetProtocol, Session):
    """
    Each player connecting over telnet (ie using most traditional mud
    clients) gets a telnet protocol instance assigned to them.  All
    communication between game and player goes through here.
    """
    def connectionMade(self):
        """
        This is called when the connection is first
        established.
        """
        # initialize the session
        self.iaw_mode = False
        client_address = self.transport.client
        # this number is counted down for every handshake that completes.
        # when it reaches 0 the portal/server syncs their data
        self.handshakes = 5 # naws, ttype, mccp, mssp, msdp
        self.init_session("telnet", client_address, self.factory.sessionhandler)

        # negotiate client size
        self.naws = naws.Naws(self)
        # negotiate ttype (client info)
        # Obs: mudlet ttype does not seem to work if we start mccp before ttype. /Griatch
        self.ttype = ttype.Ttype(self)
        # negotiate mccp (data compression) - turn this off for wireshark analysis
        self.mccp = Mccp(self)
        # negotiate mssp (crawler communication)
        self.mssp = mssp.Mssp(self)
        # msdp
        self.msdp = msdp.Msdp(self)
        # add this new connection to sessionhandler so
        # the Server becomes aware of it.
        self.sessionhandler.connect(self)

        # timeout the handshakes in case the client doesn't reply at all
        from src.utils.utils import delay
        delay(2, callback=self.handshake_done, retval=True)

    def handshake_done(self, force=False):
        """
        This is called by all telnet extensions once they are finished.
        When all have reported, a sync with the server is performed.
        The system will force-call this sync after a small time to handle
        clients that don't reply to handshakes at all.
        info - debug text from the protocol calling
        """
        if self.handshakes > 0:
            if force:
                self.sessionhandler.sync(self)
                return
            self.handshakes -= 1
            if self.handshakes <= 0:
                # do the sync
                self.sessionhandler.sync(self)

    def enableRemote(self, option):
        """
        This sets up the remote-activated options we allow for this protocol.
        """
        pass
        return (option == LINEMODE or
                option == ttype.TTYPE or
                option == naws.NAWS or
                option == MCCP or
                option == mssp.MSSP)

    def enableLocal(self, option):
        """
        Call to allow the activation of options for this protocol
        """
        return (option == MCCP or option==ECHO)

    def disableLocal(self, option):
        """
        Disable a given option
        """
        if option == ECHO:
            return True
        if option == MCCP:
            self.mccp.no_mccp(option)
            return True
        else:
            return super(TelnetProtocol, self).disableLocal(option)

    def connectionLost(self, reason):
        """
        this is executed when the connection is lost for
        whatever reason. it can also be called directly, from
        the disconnect method
        """
        self.sessionhandler.disconnect(self)
        self.transport.loseConnection()

    def dataReceived(self, data):
        """
        This method will split the incoming data depending on if it
        starts with IAC (a telnet command) or not. All other data will
        be handled in line mode. Some clients also sends an erroneous
        line break after IAC, which we must watch out for.

        OOB protocols (MSDP etc) already intercept subnegotiations
        on their own, never entering this method. They will relay
        their parsed data directly to self.data_in.

        """

        if data and data[0] == IAC or self.iaw_mode:
            try:
                #print "IAC mode"
                super(TelnetProtocol, self).dataReceived(data)
                if len(data) == 1:
                    self.iaw_mode = True
                else:
                    self.iaw_mode = False
                return
            except Exception, err1:
                conv = ""
                try:
                    for b in data:
                        conv += " " + repr(ord(b))
                except Exception, err2:
                    conv = str(err2) + ":", str(data)
                out = "Telnet Error (%s): %s (%s)" % (err1, data, conv)
                logger.log_trace(out)
                return
        # if we get to this point the command must end with a linebreak.
        # We make sure to add it, to fix some clients messing this up.
        data = data.rstrip("\r\n") + "\n"
        #print "line data in:", repr(data)
        StatefulTelnetProtocol.dataReceived(self, data)

    def _write(self, data):
        "hook overloading the one used in plain telnet"
        # print "_write (%s): %s" % (self.state,  " ".join(str(ord(c)) for c in data))
        data = data.replace('\n', '\r\n').replace('\r\r\n', '\r\n')
        #data = data.replace('\n', '\r\n')
        super(TelnetProtocol, self)._write(mccp_compress(self, data))

    def sendLine(self, line):
        "hook overloading the one used by linereceiver"
        #print "sendLine (%s):\n%s" % (self.state, line)
        #escape IAC in line mode, and correctly add \r\n
        line += self.delimiter
        line = line.replace(IAC, IAC + IAC).replace('\n', '\r\n')
        return self.transport.write(mccp_compress(self, line))

    def lineReceived(self, string):
        """
        Telnet method called when data is coming in over the telnet
        connection. We pass it on to the game engine directly.
        """
        self.data_in(text=string)

    # Session hooks

    def disconnect(self, reason=None):
        """
        generic hook for the engine to call in order to
        disconnect this protocol.
        """
        if reason:
            self.data_out(reason)
        self.connectionLost(reason)

    def data_in(self, text=None, **kwargs):
        """
        Data Telnet -> Server
        """
        self.sessionhandler.data_in(self, text=text, **kwargs)

    def data_out(self, text=None, **kwargs):
        """
        Data Evennia -> Player.
        generic hook method for engine to call in order to send data
        through the telnet connection.

        valid telnet kwargs:
            oob=<string> - supply an Out-of-Band instruction.
            xterm256=True/False - enforce xterm256 setting. If not
                                  given, ttype result is used. If
                                  client does not suport xterm256, the
                                  ansi fallback will be used
            ansi=True/False - enforce ansi setting. If not given,
                              ttype result is used.
            nomarkup=True - strip all ansi markup (this is the same as
                            xterm256=False, ansi=False)
            raw=True - pass string through without any ansi
                       processing (i.e. include Evennia ansi markers but do
                       not convert them into ansi tokens)
            prompt=<string> - supply a prompt text which gets sent without a
                              newline added to the end
            echo=True/False
        The telnet ttype negotiation flags, if any, are used if no kwargs
        are given.
        """
        try:
            text = utils.to_str(text if text else "", encoding=self.encoding)
        except Exception, e:
            self.sendLine(str(e))
            return
        if "oob" in kwargs:
            oobstruct = self.sessionhandler.oobstruct_parser(kwargs.pop("oob"))
            if "MSDP" in self.protocol_flags:
                for cmdname, args, kwargs in oobstruct:
                    #print "cmdname, args, kwargs:", cmdname, args, kwargs
                    msdp_string = self.msdp.evennia_to_msdp(cmdname, *args, **kwargs)
                    #print "msdp_string:", msdp_string
                    self.msdp.data_out(msdp_string)

        # parse **kwargs, falling back to ttype if nothing is given explicitly
        ttype = self.protocol_flags.get('TTYPE', {})
        xterm256 = kwargs.get("xterm256", ttype.get('256 COLORS', False) if ttype.get("init_done") else True)
        useansi = kwargs.get("ansi", ttype and ttype.get('ANSI', False) if ttype.get("init_done") else True)
        raw = kwargs.get("raw", False)
        nomarkup = kwargs.get("nomarkup", not (xterm256 or useansi))
        prompt = kwargs.get("prompt")
        echo = kwargs.get("echo", None)

        #print "telnet kwargs=%s, message=%s" % (kwargs, text)
        #print "xterm256=%s, useansi=%s, raw=%s, nomarkup=%s, init_done=%s" % (xterm256, useansi, raw, nomarkup, ttype.get("init_done"))
        if raw:
            # no processing whatsoever
            self.sendLine(text)
        elif text:
            # we need to make sure to kill the color at the end in order
            # to match the webclient output.
            #print "telnet data out:", self.protocol_flags, id(self.protocol_flags), id(self), "nomarkup: %s, xterm256: %s" % (nomarkup, xterm256)
            self.sendLine(ansi.parse_ansi(_RE_N.sub("", text) + "{n", strip_ansi=nomarkup, xterm256=xterm256))

        if prompt:
            # Send prompt separately
            prompt = ansi.parse_ansi(_RE_N.sub("", prompt) + "{n", strip_ansi=nomarkup, xterm256=xterm256)
            prompt = prompt.replace(IAC, IAC + IAC).replace('\n', '\r\n')
            prompt += IAC + GA
            self.transport.write(mccp_compress(self, prompt))
        if echo:
            self.transport.write(mccp_compress(self, IAC+WONT+ECHO))
        elif echo == False:
            self.transport.write(mccp_compress(self, IAC+WILL+ECHO))

