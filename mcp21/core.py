import re, random, os, importlib

# This module was developed by squinting directly at both the MCP spec
# at http://www.moo.mud.org/mcp2/mcp2.html and tkMOO-light's plugins/mcp21.tcl
# file, to which this code bears more than a little resemblance and owes
# more than a little debt.

OOB_PREFIX   = re.compile('^#\$#')
QUOTE_PREFIX = re.compile('^#\$"')

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

def _version_cmp(v1, v2):
    v1_maj, v1_min = re.split('\.', v1)
    v2_maj, v2_min = re.split('\.', v2)

    return (v1_maj > v2_maj or (v1_maj == v2_maj and v1_min >= v2_min));

class MCPCore:
    def __init__(self, conn):
        self.multiline_messages = {}
        self.mcp_active = 0
        self.mcp_auth_key = ''
        self.connection = conn

        self.msg_registry = {}
        self.packages = {}

        MCP(self) # initialize the 'mcp' core package

        # walk the packages directory, and instantiate everything we find there.
        # this relies on each package having a class called "MCPPackage" that's a
        # sane and correct subclass of MCPPackageBase.
        for package_file in os.listdir("./mcp21/package"):
            package, ext = package_file.split('.')

            if package == '__init__' or ext != 'py' : continue

            # do the actual importing
            mod = importlib.import_module('mcp21.package.' + package)

            # then go find the thing called "MCPPackage" (the subclass constructor) and call it
            getattr(mod, 'MCPPackage')(self)

    def debug(self, info):
        info = re.sub('\n$', '', info)
        # DebugMCP window monkey-patches this when it shows itself
        # TODO - we might want one debug window per-connection-window
        print(self.connection.world.get('name') + ": " + info)

    def output_filter(self, data):
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
        self.debug("S->C: #$#" + data)

        m = re.match(r'(\S+)\s*(.*)', data)

        message_name, rest = m.group(1,2)

        # if we haven't started yet, and the message isn't a startup negotiation...
        if (not self.mcp_active and message_name != 'mcp'): return

        # multiline message handling.  This is awful.
        if message_name == '*':
            m = re.match(r'^(\S*) ([^:]*): (.*)', rest)
            tag, field, value = m.group(1,2,3)

            message = self.multiline_messages[tag]
            message._data_tag = tag

            if not field in message.data: message.data[field] = []

            message.data[field].append(value)

        elif message_name == ':':
            m = re.match(r'^(\S+)', rest)
            tag = m.group(1)
            message = self.multiline_messages[tag]
            message.multi_in_progress = False
        else:
            message = self.parse(rest)

        # check auth
        if (message_name != '*') and (message_name != 'mcp') and (message.auth_key != self.mcp_auth_key):
            self.debug("mcp - auth failed")
            return

        message.message = message.message or message_name

        if message.multi_in_progress:
            if not self.multiline_messages.has_key(message._data_tag):
                self.multiline_messages[message._data_tag] = message
        else:
            # don't dispatch multilines in progress
            self.dispatch(message)

        # return void/falsy/None so the output widget skips this line
        return

    def parse(self, raw):

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
            m = re.match(r'^(.+)(\*)', keyword)
            if m:
                keyword, splat = m.group(1,2)

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

    def dispatch(self, message):
        package = self.msg_registry.get(message.message)
        if not package: return

        if package.activated: package.dispatch(message)

    def server_notify(self, msg, args = {}):

        out = "#$#" + msg + " " + self.mcp_auth_key

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

        self.server_send(out)

        if multiline:
            for k in multiline:
                l = multiline[k]
                for line in l:
                    self.server_send("#$#* " + datatag + " " + k + ": " + line)
                self.server_send("#$#: " + datatag)

    def server_send(self, out_line):
        self.connection.output(out_line)
        self.debug("C->S: " + out_line)

    def start_mcp(self):
        for p in self.packages.values():
            p.Initialize()

    def register(self, pkg, messages):
        if not isinstance(pkg, MCPPackageBase):
            print("something that isn't an MCP package tried to register")
            return
        self.packages[pkg.package] = pkg
        for message in messages:
            self.msg_registry[message] = pkg

    # next two subs taken from MCP 2.1 specification, section 2.4.3
    def get_best_version(self, pkg, smin, smax):
        if not self.packages.has_key(pkg): return

        cmax = self.packages[pkg].max
        cmin = self.packages[pkg].min

        if (_version_cmp(cmax, smin) and _version_cmp(smax, cmin)):
            if _version_cmp(smax, cmax):
                return cmax
            else:
                return smax
        else:
            return undef
### "MCP" package to get MCP itself enfired
### we put this here because it needs/provides special bootstrapping that the
### other packages don't

from mcp21.package import MCPPackageBase
class MCP(MCPPackageBase):
    def __init__(self, mcp):
        self.package   = 'mcp'
        self.min       = 2.1
        self.max       = 2.1
        self.activated = 2.1
        self.mcp       = mcp

        mcp.register(self, ['mcp'])

    def dispatch(self, message):
        if re.search('mcp', message.message): self.do_mcp(message)

    ### handlers
    def do_mcp(self, message):
        if message.data['version'] == 2.1 or message.data['to'] >= 2.1:
            self.mcp.mcp_active = True
        else:
            self.mcp.debug("mcp version doesn't match, bailing")
            return;

        # we both support 2.1 - ship the server a key and start haggling
        key = str(os.getpid())
        self.mcp.mcp_auth_key = key
        self.mcp.server_send("#$#mcp authentication-key: "+key+" version: 2.1 to: 2.1")

        self.mcp.start_mcp()

    def Initialize(wuh): pass

class Message:
    def __init__(self):
        self.data              = {}
        self._data_tag         = None
        self.message           = ''
        self.multi_in_progress = False
