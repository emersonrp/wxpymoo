# This handles the TTYPE request per the MTTS spec (https://tintin.sourceforge.io/protocols/mtts/)

MTTS = chr(24)  # terminal type
IAC   = chr(255) # "Interpret As Command"
SE    = chr(240) # Subnegotiation End
SB    = chr(250) # Subnegotiation Begin

# Our bitvector for MTTS:
#   1 "ANSI"              Client supports all common ANSI color codes.
#   2 "VT100"             Client supports all common VT100 codes.
#   4 "UTF-8"             Client is using UTF-8 character encoding.
#   8 "256 COLORS"        Client supports all 256 color codes.
# 256 "TRUECOLOR"         Client supports all truecolor codes.
#
# 256 + 8 + 4 + 2 + 1 == 271

# TODO maybe someday:
# 16 "MOUSE TRACKING"    Client supports xterm mouse tracking.
# 32 "OSC COLOR PALETTE" Client supports the OSC color palette.

replies = [ 'WXPYMOO', 'VT100-TRUECOLOR', 'MTTS 271', 'MTTS 271' ]

def handle_mtts(payload, conn):

    conn.mtts_reply = getattr(conn, 'mtts_reply', 0)
    reply = replies[conn.mtts_reply]

    print("Got IAC MTTS subrequest;  Sending " + reply)
    conn.output(IAC + SB + MTTS + chr(0) + reply + IAC + SE)

    # Bump to the next element, but start over if we run off the end.
    conn.mtts_reply += 1
    if conn.mtts_reply > len(replies)-1:
        conn.mtts_reply = 0
