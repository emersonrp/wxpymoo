import wx
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver

from window.mainsplitter import MainSplitter
from window.inputpane import InputPane
from window.outputpane import OutputPane
import mcp21.core as mcp21

class ConnectionClient(LineReceiver):
    def lineReceived(self, line):
        self.factory.connection.output_pane.display(line)

    def output(self, line):
        self.sendLine(str(line))

    def connectionMade(self):
        self.connected = True
        # turn on TCP keepalive if possible
        try:
            self.transport.setTcpKeepAlive(1)
        except AttributeError: pass

    def connectionLost(self, reason):
        self.connected = False

class ConnectionClientFactory(ClientFactory):
    def __init__(self, connection):
        self.connection = connection
        self.protocol   = ConnectionClient

    def buildProtocol(self, addr):
        p = ClientFactory.buildProtocol(self, addr)
        self.connection.input_receiver = p
        return p

    #def clientConnectionFailed(self, connector, reason):
        #print("connection failed:", reason.getErrorMessage())
        #reactor.stop()

    #def clientConnectionLost(self, connector, reason):
        #print('connection lost:', reason.getErrorMessage())
        #reactor.stop()


class Connection:
    def __init__(self, mainwindow):
        self.host = ''
        self.port = ''
        #self.keepalive = Keepalive(self)
        self.input_receiver = None

        self.connector = None
        self.mainwindow = mainwindow

        # the UI components for this connection
        self.splitter    = MainSplitter(mainwindow.tabs)
        self.input_pane  = InputPane(self)
        self.output_pane = OutputPane(self)

        self.splitter.SplitHorizontally(self.output_pane, self.input_pane)
        self.splitter.SetMinimumPaneSize(20); # TODO - set to "one line of input field"

    def Close(self):
        if self.input_receiver.connected:
            self.output_pane.display("WxMOO: Connection closed.\n");
        # force it again just to be sure
        #self.keepalive.Stop()
        self.connector.disconnect()

    # connection.connect ([host], [port])
    #
    # existing connections will remember their host and port if not supplied here,
    # for ease of reconnect etc.
    def connect(self, host, port):
        self.host = host
        self.port = port
        self.connector = reactor.connectTCP(self.host, self.port, ConnectionClientFactory(self))

        mcp21.Initialize(self)

        # TODO - 'if world.connection.keepalive'
        #self.keepalive.Start()

    def output(self, stuff):
        self.input_receiver.output(stuff)

    def reconnect(self):
        if self.connector: self.Close()
        self.connect(self.host, self.port)

class Keepalive(wx.EvtHandler):
    ######################
    # This is a stupid brute-force keepalive that periodically tickles the
    # connection by sending a single space.  Not magical or brilliant.
    def __init__(self, connection):
        wx.EvtHandler.__init__(self)
        self.connection = connection
        self.timer = wx.Timer()

        self.timer.Bind(wx.EVT_TIMER, self.on_keepalive)

    def Start(self):
        self.timer.Start(60000, False) # 1 minute TODO make this a pref?

    def Stop(self):
        self.timer.Stop()

    def on_keepalive(self, evt):
        # TODO - this is pretty brute-force, innit?
        # This'll likely break on worlds that actually
        # are character-based instead of line-based.
        self.connection.output(" ")
