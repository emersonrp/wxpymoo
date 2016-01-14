import wx
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
#use WxMOO::MCP21;  # this is icky

from wxpymoo.window.mainsplitter import MainSplitter
from wxpymoo.window.inputpane import InputPane
from wxpymoo.window.outputpane import OutputPane

# TODO - should an output_pane own a connection, or vice-versa?
# This is related to the answer to "do we want multiple worlds to be
# open in like tabs or something?"

class ConnectionClient(LineReceiver):
    def lineReceived(self, line):
        self.factory.connection.output_pane.display(line)

    def output(self, line):
        self.sendLine(str(line))

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
        self.post = ''
        self.keepalive = Keepalive()
        self.input_receiver = None

        # the UI components for this connection
        self.splitter    = MainSplitter(mainwindow.tabs)
        self.input_pane  = InputPane(self)
        self.output_pane = OutputPane(self)

        self.splitter.SplitHorizontally(self.output_pane, self.input_pane)
        self.splitter.SetMinimumPaneSize(20); # TODO - set to "one line of input field"

    def Close(self):
        #self.SUPER::Close;
        #self.output_pane.display("WxMOO: Connection closed.\n");
        self.keepalive.Stop

    # connection.connect ([host], [port])
    #
    # existing connections will remember their host and port if not supplied here,
    # for ease of reconnect etc.
    def connect(self, host, port):
        if host: self.host = host
        if port: self.port = port
        reactor.connectTCP(self.host, self.port, ConnectionClientFactory(self))

        # Ugh.  I'm gonna have to build my own event dispatch system, aren't I
        # WxMOO::MCP21::new_connection($self);

        # TODO - 'if world.connection.keepalive'
        # self.keepalive.Start()

    def output(self, stuff):
        self.input_receiver.output(stuff)

    def reconnect(self):
        #self.Close if self.IsConnected()
        self.connect()

class Keepalive(wx.Timer):
    ######################
    # This is a stupid brute-force keepalive that periodically tickles the
    # connection by sending a single space.  Not magical or brilliant.
    KEEPALIVE_TIME = 60000  # 1 minute
    def new(self, connection, timeout = KEEPALIVE_TIME):
        wx.Timer.__init__(self)
        self.connection = connection
        self.timeout    = timeout

        self.Bind(wx,EVT_TIMER, self.on_keepalive)

    def Start(self):
        wx.Timer.Start(self, self.timeout, False)

    def on_keepalive(self):
        # TODO - this is pretty brute-force, innit?
        # This'll likely break on worlds that actually
        # are character-based instead of line-based.
        self.connection.Write(" ")
