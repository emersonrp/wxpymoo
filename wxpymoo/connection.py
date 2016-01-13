import wx
from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
#use WxMOO::MCP21;  # this is icky

# TODO - should an output_pane own a connection, or vice-versa?
# This is related to the answer to "do we want multiple worlds to be
# open in like tabs or something?"

class ConnectionClient(LineReceiver):
    def lineReceived(self, line):
        print(line)
        #self.output_pane.display(line)

    def output(self, rest):
        self.sendLine(rest)

class ConnectionClientFactory(ClientFactory):
    protocol = ConnectionClient

    def __init__(self):
        self.done = Deferred()

    def clientConnectionFailed(self, connector, reason):
        print("connection failed:", reason.getErrorMessage())
        self.done.errback(reason)

    def clientConnectionLost(self, connector, reason):
        print('connection lost:', reason.getErrorMessage())
        self.done.callback(None)


class Connection:

    def __init__(self, mainwindow):
        self.host = ''
        self.post = ''
        self.output_pane = mainwindow.output_pane

    def Close(self):
        #self.keepalive.Stop;
        #self.SUPER::Close;
        #self.output_pane.display("WxMOO: Connection closed.\n");
        pass

    def main(self, reactor):
        factory = ConnectionClientFactory()
        reactor.connectTCP(self.host, self.port, factory)
        return factory.done

    # connection.connect ([host], [port])
    #
    # existing connections will remember their host and port if not supplied here,
    # for ease of reconnect etc.
    def connect(self, host, port):

        if host: self.host = host
        if port: self.port = port

        factory = ClientFactory()
        task.react(self.main)


    def gotProtocol(p):
        self.input_pane.connection = self
        # Ugh.  I'm gonna have to build my own event dispatch system, aren't I
        # WxMOO::MCP21::new_connection($self);
        # TODO - 'if world.connection.keepalive'
        self.init_keepalive()

    def reconnect(self):
        #self.Close if self.IsConnected()
        self.connect()

    KEEPALIVE_TIME = 60000  # 1 minute
    def init_keepalive(self):
        self.keepalive = WxMOO.Connection.Keepalive(self)
        self.keepalive.Start(KEEPALIVE_TIME, 0)


######################
# This is a stupid brute-force keepalive that periodically tickles the
# connection by sending a single space.  Not magical or brilliant.
# 
#     package WxMOO::Connection::Keepalive;
# 
#     use parent 'Wx::Timer';
#     use Wx::Event qw( EVT_TIMER );
# 
#     def new {
#         my ($class, $connection) = @_;
#         my $self = $class.SUPER::new;
#         $self.{'connection'} = $connection;
# 
#         EVT_TIMER($self, -1, \&on_keepalive);
# 
#         bless $self, $class;
# 
# # TODO - this is pretty brute-force, innit?
# # This'll likely break on worlds that actually
# # are character-based instead of line-based.
#     def on_keepalive {
#         shift.{'connection'}.Write(" ");
# 
