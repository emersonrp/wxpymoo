import re, random, os, importlib

import mcp21.registry as registry

# This module was developed by squinting directly at both the MCP spec
# at http://www.moo.mud.org/mcp2/mcp2.html and tkMOO-light's plugins/mcp21.tcl
# file, to which this code bears more than a little resemblance and owes
# more than a little debt.

OOB_PREFIX   = re.compile('^#\$#')
QUOTE_PREFIX = re.compile('^#\$"')

# TODO - these -work- as package-scope vars, but might want some better encapsulation
# later on.  tkmoo has the notion of a request object that it stashes them in.
mcp_active = 0
mcp_auth_key = ''
connection = None

# This is probably the right place for this, though.
multiline_messages = {}

def Initialize(conn):

    global connection
    if conn: connection = conn

    MCP() # initialize the 'mcp' core package

    # walk the packages directory, and instantiate everything we find there.
    # this relies on each package having a class called "MCPPackage" that's a
    # sane and correct subclass of MCPPackageBase.
    for package_file in os.listdir("./mcp21/package"):
        package, ext = package_file.split('.')

        if package == '__init__' or ext != 'py' : continue

        # do the actual importing
        mod = importlib.import_module('mcp21.package.' + package)

        # then go find the thing called "MCPPackage" (the subclass constructor) and call it
        getattr(mod, 'MCPPackage')()

def debug(info):
    info = re.sub('\n$', '', info)
    # DebugMCP window monkey-patches this when it shows itself
    # TODO - we might want one debug window per-connection-window
    print(info)

def output_filter(data):
    # MCP spec, 2.1:
    # A received network line that begins with the characters #$# is translated
    # to an out-of-band (MCP message) line consisting of exactly the same
    # characters.  A received network line that begins with the characters #$"
    # must be translated to an in-band line consisting of the network line with
    # the prefix #$" removed.  Any other received network line translates to an
    # in-band line consisting of exactly the same characters.

    data, matches = QUOTE_PREFIX.subn('', data)  # did we have the quote prefix?
    if matches > 0: return data                  # we did, and removed it.  Return the line

    data, matches = OOB_PREFIX.subn('', data) # did we have the oob prefix?
    if matches == 0: return data              # we did not, so return the line and bail

    # now we have only lines that started with OOB_PREFIX, which has been trimmed
    debug("S->C: #$#" + data)

    m = re.match(r'(\S+)\s*(.*)', data)

    message_name, rest = m.group(1,2)

    # if we haven't started yet, and the message isn't a startup negotiation...
    if (not mcp_active and message_name != 'mcp'): return

    # multiline message handling.  This is awful.
    if message_name == '*':
        m = re.match(r'^(\S*) ([^:]*): (.*)', rest)
        tag, field, value = m.group(1,2,3)

        message = multiline_messages[tag]
        message._data_tag = tag

        if not field in message.data: message.data[field] = []

        message.data[field].append(value)

    elif message_name == ':':
        m = re.match(r'^(\S+)', rest)
        tag = m.group(1)
        message = multiline_messages[tag]
        message.multi_in_progress = False
    else:
        message = parse(rest)

    # check auth
    if (message_name != '*') and (message_name != 'mcp') and (message.auth_key != mcp_auth_key):
        debug("mcp - auth failed")
        return

    message.message = message.message or message_name

    if message.multi_in_progress:
        if not multiline_messages.has_key(message._data_tag):
            multiline_messages[message._data_tag] = message
    else:
        # don't dispatch multilines in progress
        dispatch(message)

    # always return undef so the output widget skips this line
    return

#    my $simpleChars = q|[-a-z0-9~`!@#$%^&*()=+{}[\]\|';?/><.,]|;
#    while ($raw =~ /([-_*a-z0-9]+)              # keyword
#                        :                       # followed by colon
#                        \s+                     # some space
#                        (                       # and either
#                            (?:"[^"]*")         # a quoted string - TODO - the grammar is more picky than [^"]
#                            |                   # or
#                            (?:$simpleChars)+   # a value
#                        )/igx)
raw_re = re.compile(r'([-_*a-z0-9]+):\s+((?:"[^"]*")|(?:[-a-z0-9~`!@#$%^&*()=+{}[\]\|\';?/><.,])+)')

def parse(raw):

    if not raw: return

    first = re.split('\s+', raw)[0]

    message = Message()

    if not re.search(r':$', first):
        message.auth_key = first
        first_re = '^' + re.escape(first) + '\s+'
        raw = re.sub(first_re, '', raw)

    keyvals = re.findall(raw_re, raw)

    for keyval in keyvals:
        keyword, value = keyval
        if re.search('\*$', keyword):
            message.data[keyword] = []
            message.multi_in_progress = True
        elif keyword == '_data-tag':
            message._data_tag = value
        else:
            # if we have a double-quoted string, strip the quotes
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            message.data[keyword] = value

    return message

def dispatch(message):
    package = registry.msg_registry.get(message.message)
    if not package: return

    if package.activated: package.dispatch(message)

def server_notify(msg, args = {}):

    out = "#$#" + msg + " " + mcp_auth_key

    multiline = {}

    for k in args:
        # TODO escape v if needed
        v = args[k] or ''

        if type(v) is list: # multiline!
            multiline[k] = v
            datatag = str(random.randint(1,1000000))
            out += " " + k + '*: "" _data-tag: ' + datatag
        else :
            out += ' ' + k + ': "' + v + '"'

    server_send(out)

    if multiline:
        for k in multiline:
            l = multiline[k]
            for line in l:
                server_send("#$#* " + datatag + " " + k + ": " + line)
            server_send("#$#: " + datatag)

def server_send(out_line):
    connection.output(out_line)
    debug("C->S: " + out_line)

def start_mcp():
    for p in registry.packages.values():
        p.Initialize()

### "MCP" package to get MCP itself enfired
### we put this here because it needs/provides special bootstrapping that the
### other packages don't

from mcp21.package import MCPPackageBase
class MCP(MCPPackageBase):
    def __init__(self):
        self.package   = 'mcp'
        self.min       = 2.1
        self.max       = 2.1
        self.activated = 2.1

        registry.register(self, ['mcp'])

    def dispatch(self, message):
        if re.search('mcp', message.message): self.do_mcp(message)

    ### handlers
    def do_mcp(self, message):
        import os
        import mcp21.core as mcp21

        if message.data['version'] == 2.1 or message.data['to'] >= 2.1:
            mcp21.mcp_active = True
        else:
            mcp21.debug("mcp version doesn't match, bailing")
            return;

        # we both support 2.1 - ship the server a key and start haggling
        key = str(os.getpid())
        mcp21.mcp_auth_key = key
        mcp21.server_send("#$#mcp authentication-key: "+key+" version: 2.1 to: 2.1")

        mcp21.start_mcp()

    def Initialize(wuh): pass

class Message:
    def __init__(self):
        self.data              = {}
        self._data_tag         = None
        self.message           = ''
        self.multi_in_progress = False
