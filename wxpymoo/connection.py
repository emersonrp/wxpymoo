import wx
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
#use Wx::Event qw( EVT_SOCKET_INPUT EVT_TIMER );
#use WxMOO::MCP21;  # this is icky

# TODO - should an output_pane own a connection, or vice-versa?
# This is related to the answer to "do we want multiple worlds to be
# open in like tabs or something?"

class Connection(Protocol):
    def __init__(self, parent):
        #self.output_pane = parent.output_pane
        #self.input_pane  = parent.input_pane
        pass

    def dataReceived(self, data):
        self.output_pane.display(data)

    def Close(self):
        #self.keepalive.Stop;
        #self.SUPER::Close;
        #self.output_pane.display("WxMOO: Connection closed.\n");
        pass

    def output(self, rest):
        self.transport.write(rest)


# $connection.connect ([host], [port])
#
# existing connections will remember their host and port if not supplied here,
# for ease of reconnect etc.
    def connect(self, host, port):
        if host: self.host = host
        if port: self.port = port

        self.endpoint = TCP4ClientEndpoint(reactor, self.host, self.port)
        d = connectProtocol(self.endpoint, Connection())
        d.addCallback(gotProtocol)

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
