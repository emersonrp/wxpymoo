import re

import wxpymoo.mcp21.registry as registry

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
connection = ''

# This is probably the right place for this, though.
multiline_messages = {}

#  # We'd like to enumerate this automatically.
#  use WxMOO::MCP21::Package::mcp
#  #use WxMOO::MCP21::Package::mcp_cord
#  use WxMOO::MCP21::Package::mcp_negotiate
#  use WxMOO::MCP21::Package::dns_org_mud_moo_simpleedit
#  use WxMOO::MCP21::Package::dns_com_awns_status
#  
#  my $pkg_mcp            = WxMOO::MCP21::Package::mcp          ->new
#  #my $pkg_mcp_cord       = WxMOO::MCP21::Package::mcp_cord     ->new
#  my $pkg_mcp_negotiate  = WxMOO::MCP21::Package::mcp_negotiate->new
#  my $pkg_mcp_simpleedit = WxMOO::MCP21::Package::dns_org_mud_moo_simpleedit->new
#  my $pkg_mcp_status     = WxMOO::MCP21::Package::dns_com_awns_status->new

def debug(info):
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

    message = {};  # here's where we decode this

    # multi-line message handling.  This is awful.
    if message_name == '*':
        m = re.match(r'^(\S*) ([^:]*): (.*)', rest)
        tag, field, value = m.group(1,2,3)

        message = multiline_messages[tag]
        message['_data-tag'] = tag

        message['data'][field].append(value)
    elif message_name == ':':
        m = re.match(r'^(\S+)', rest)
        tag = m.group(1)
        message = multiline_messages[tag]
        message.delete('multi_in_progress')
    else:
        message = parse(rest)

    # check auth
    if (message_name != '*') and (message_name != 'mcp') and (message['auth_key'] != mcp_auth_key):
        debug("mcp - auth failed")
        return

    if not message.has_key('message'):
        message['message'] = message_name

    if message['multi_in_progress']:
        multiline_messages[message['_data-tag']] = (multiline_messages[message['_data-tag']] or message)
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
    message = {
        'data': {},
        'multi_in_progress' : False,
    }

    if not re.search(r':$', first):
        message['auth_key'] = first
        first_re = r"^" + re.escape(first) + r"\s+"
        raw = first_re.sub('', raw)

    keyvals = re.findall(raw_re, raw)

    for keyval in keyvals:
        keyword, value = keyval
        if re.search('\*$', keyword):
            message['data'][keyword] = []
            message['multi_in_progress'] = 1
        elif keyword == '_data-tag':
            message['_data-tag'] = value
        else:
            message['data'][keyword] = value

    return message

def dispatch(message):
    package = registry.msg_registry.get(message['message'])
    if not package: return

    if package.activated: package.dispatch(message)

def server_notify(msg, args):

    out = "#$#" + msg + " " + key

    for k in args:
        # TODO escape v if needed
        v = args[k] or ''

        if type(v) is dict: # multiline!
            multiline[k] = v
            datatag = int(rand(1000000))
            out += k + '*: "" _data-tag: ' + datatag
        else :
            out += k + ": " + v

    debug("C->S: " + out)
    connection.Write(out + "\n")

    if multiline:
        for k in multiline:
            l = multiline[k]
            for line in l:
                out_line = "#$#* " + datatag + " " + k + ": " + line + "\n"
                connection.Write(out_line)
                debug(out_line)
            connection.Write("#$#: " + datatag + "\n")
            debug("#$#: " + datatag)

def new_connection(conn):
    global connection
    connection = conn

def start_mcp():
    for p in registry.packages:
        p._init
