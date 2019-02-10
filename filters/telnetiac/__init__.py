r"""TELNET negotiation filter

This code was adapted from the telnetlib library included with Python 2.7,
and is being used under the PSF License agreement included below.

All changes to the original telnetlib code are copyright (c) 2019 R Pickett,
and licensed under the same terms.

======================================
1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and
   the Individual or Organization ("Licensee") accessing and otherwise using Python
   2.7.15 software in source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
   grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
   analyze, test, perform and/or display publicly, prepare derivative works,
   distribute, and otherwise use Python 2.7.15 alone or in any derivative
   version, provided, however, that PSF's License Agreement and PSF's notice of
   copyright, i.e., "Copyright © 2001-2019 Python Software Foundation; All Rights
   Reserved" are retained in Python 2.7.15 alone or in any derivative version
   prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on or
   incorporates Python 2.7.15 or any part thereof, and wants to make the
   derivative work available to others as provided herein, then Licensee hereby
   agrees to include in any such work a brief summary of the changes made to Python
   2.7.15.

4. PSF is making Python 2.7.15 available to Licensee on an "AS IS" basis.
   PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED.  BY WAY OF
   EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR
   WARRANTY OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE
   USE OF PYTHON 2.7.15 WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON 2.7.15
   FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT OF
   MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 2.7.15, OR ANY DERIVATIVE
   THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material breach of
   its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any relationship
   of agency, partnership, or joint venture between PSF and Licensee.  This License
   Agreement does not grant permission to use PSF trademarks or trade name in a
   trademark sense to endorse or promote products or services of Licensee, or any
   third party.

8. By copying, installing or otherwise using Python 2.7.15, Licensee agrees
   to be bound by the terms and conditions of this License Agreement.
======================================
"""

from collections import deque
import wx

# Telnet protocol characters (don't change)
IAC  = chr(255) # "Interpret As Command"
DONT = chr(254)
DO   = chr(253)
WONT = chr(252)
WILL = chr(251)
theNULL = chr(0)

SE  = chr(240)  # Subnegotiation End
NOP = chr(241)  # No Operation
DM  = chr(242)  # Data Mark
BRK = chr(243)  # Break
IP  = chr(244)  # Interrupt process
AO  = chr(245)  # Abort output
AYT = chr(246)  # Are You There
EC  = chr(247)  # Erase Character
EL  = chr(248)  # Erase Line
GA  = chr(249)  # Go Ahead
SB =  chr(250)  # Subnegotiation Begin

# IAC

# Telnet protocol options code (don't change)
# These ones all come from arpa/telnet.h
BINARY = chr(0) # 8-bit data path
ECHO = chr(1) # echo
RCP = chr(2) # prepare to reconnect
SGA = chr(3) # suppress go ahead
NAMS = chr(4) # approximate message size
STATUS = chr(5) # give status
TM = chr(6) # timing mark
RCTE = chr(7) # remote controlled transmission and echo
NAOL = chr(8) # negotiate about output line width
NAOP = chr(9) # negotiate about output page size
NAOCRD = chr(10) # negotiate about CR disposition
NAOHTS = chr(11) # negotiate about horizontal tabstops
NAOHTD = chr(12) # negotiate about horizontal tab disposition
NAOFFD = chr(13) # negotiate about formfeed disposition
NAOVTS = chr(14) # negotiate about vertical tab stops
NAOVTD = chr(15) # negotiate about vertical tab disposition
NAOLFD = chr(16) # negotiate about output LF disposition
XASCII = chr(17) # extended ascii character set
LOGOUT = chr(18) # force logout
BM = chr(19) # byte macro
DET = chr(20) # data entry terminal
SUPDUP = chr(21) # supdup protocol
SUPDUPOUTPUT = chr(22) # supdup output
SNDLOC = chr(23) # send location
TTYPE = chr(24) # terminal type
EOR = chr(25) # end or record
TUID = chr(26) # TACACS user identification
OUTMRK = chr(27) # output marking
TTYLOC = chr(28) # terminal location number
VT3270REGIME = chr(29) # 3270 regime
X3PAD = chr(30) # X.3 PAD
NAWS = chr(31) # window size
TSPEED = chr(32) # terminal speed
LFLOW = chr(33) # remote flow control
LINEMODE = chr(34) # Linemode option
XDISPLOC = chr(35) # X Display Location
OLD_ENVIRON = chr(36) # Old - Environment variables
AUTHENTICATION = chr(37) # Authenticate
ENCRYPT = chr(38) # Encryption option
NEW_ENVIRON = chr(39) # New - Environment variables
# the following ones come from
# http://www.iana.org/assignments/telnet-options
# Unfortunately, that document does not assign identifiers
# to all of them, so we are making them up
TN3270E = chr(40) # TN3270E
XAUTH = chr(41) # XAUTH
CHARSET = chr(42) # CHARSET
RSP = chr(43) # Telnet Remote Serial Port
COM_PORT_OPTION = chr(44) # Com Port Control Option
SUPPRESS_LOCAL_ECHO = chr(45) # Telnet Suppress Local Echo
TLS = chr(46) # Telnet Start TLS
KERMIT = chr(47) # KERMIT
SEND_URL = chr(48) # SEND-URL
FORWARD_X = chr(49) # FORWARD_X

PRAGMA_LOGON = chr(138) # TELOPT PRAGMA LOGON
SSPI_LOGON = chr(139) # TELOPT SSPI LOGON
PRAGMA_HEARTBEAT = chr(140) # TELOPT PRAGMA HEARTBEAT
EXOPL = chr(255) # Extended-Options-List
NOOPT = chr(0)

from filters.telnetiac.mtts import handle_ttype

############# MU* PROTOCOLS
# MSDP - MUD Server Data Protocol
MSDP = chr(69)

# MSSP - MUD Server Status Protocol
from filters.telnetiac.mssp import handle_mssp
MSSP = chr(70)

# MCCP - MUD Client Compression Protocol
MCCP1 = chr(85)
MCCP2 = chr(86)

# MSP - Mud Sound Protocol (https://www.zuggsoft.com/zmud/msp.htm)
MSP = chr(90)

# MXP - MUD eXtension Protocol (https://www.zuggsoft.com/zmud/mxp.htm)
MXP = chr(91)

# ZMP - Zenith MUD Protocol (http://discworld.starturtle.net/external/protocols/zmp.html)
ZMP = chr(93)

# ATCP - Achaea Telnet Client Protocol (https://www.ironrealms.com/rapture/manual/files/FeatATCP-txt.html)
ATCP = chr(200)

# GMCP - Generic MUD Communication Protocol (http://www.gammon.com.au/gmcp)
GMCP = chr(201)


def process_line(output_pane, line):
    buf = ['','']
    iacseq  = ''
    sbdataq = ''
    sb = 0
    option_callback = None
    conn = output_pane.connection
    for c in line:
        if not iacseq:
            if c == theNULL:
                continue
            if c == "\021":
                continue
            if c != IAC:
                buf[sb] = buf[sb] + c
                continue
            else:
                iacseq += c
        elif len(iacseq) == 1:
            # 'IAC: IAC CMD [OPTION only for WILL/WONT/DO/DONT]'
            if c in (DO, DONT, WILL, WONT):
                iacseq += c
                continue
            iacseq = ''
            if c == IAC:
                buf[sb] = buf[sb] + c
            else:
                if c == SB: # SB ... SE start.
                    sb = 1
                    sbdataq = ''
                elif c == SE:
                    sb = 0
                    sbdataq = sbdataq + buf[1]
                    buf[1] = ''
                    handle_iac_subnegotiation(sbdataq, conn)
        elif len(iacseq) == 2:
            cmd = iacseq[1]
            iacseq = ''
            opt = c
            if cmd in (DO, DONT):
                handle_iac_do_negotiation(cmd, opt, conn)
            elif cmd in (WILL, WONT):
                handle_iac_will_negotiation(cmd, opt, conn)
    # end loop
    return buf[0]

def handle_iac_do_negotiation(cmd, opt, conn):
    if cmd == DO:
        if opt == TTYPE:
            print("Got IAC DO TTYPE;  Sending IAC WILL TTYPE")
            conn.output(IAC + WILL + TTYPE)
        elif opt == NEW_ENVIRON:
            print("Got IAC DO NEW_ENVIRON;  Sending IAC WONT NEW_ENVIRON")
            conn.output(IAC + WONT + NEW_ENVIRON)
        elif opt == NAWS:
            print("Got IAC DO NAWS; Sending IAC WILL NAWS + x/y info")
            conn.iac['NAWS'] = True
            conn.output(IAC + WILL + NAWS)
            handle_naws(conn)
        elif opt == MXP:
            # TODO - support this eventually
            print("Got IAC DO MXP;  Sending IAC WONT MXP")
            conn.output(IAC + WONT + MXP)
        elif opt == ATCP:
            print("Got IAC DO ATCP;  Sending IAC WONT ATCP")
            conn.output(IAC + WONT + ATCP)
        else:
            print("Got an *unknown* negotiation IAC DO " + str(ord(opt)) + ", saying WONT")
            conn.output(IAC + WONT + opt)
    else:
        if opt == TTYPE:
            print("Got IAC DONT TTYPE; Resetting and sending WONT TTYPE")
            conn.ttype_reply = 0
            conn.output(IAC + WONT + TTYPE)
        elif opt == NAWS:
            print("Got IAC DONT NAWS; Sending IAC WONT NAWS")
            conn.iac['NAWS'] = False
            conn.output(IAC + WONT + NAWS)
        else:
            print("Got an *unknown* negotiation IAC DONT " + str(ord(opt)) + ", saying WONT")
            conn.output(IAC + WONT + opt)

def handle_iac_will_negotiation(cmd, opt, conn):
    if cmd == WILL:
        if opt == MSDP:
            # TODO - support this eventually
            print("Got IAC WILL MSDP;  Sending IAC DONT MSDP")
            conn.output(IAC + DONT + MSDP)
        elif opt == MSSP:
            print("Got IAC WILL MSSP;  Sending IAC DO MSSP")
            conn.output(IAC + DO + MSSP)
        elif opt == MCCP1:
            # TODO - support this eventually
            print("Got IAC WILL MCCP1;  Sending IAC DONT MCCP1")
            conn.output(IAC + DONT + MCCP1)
        elif opt == MCCP2:
            # TODO - support this eventually
            print("Got IAC WILL MCCP2;  Sending IAC DONT MCCP2")
            conn.output(IAC + DONT + MCCP2)
        elif opt == MSP:
            # TODO - support this eventually
            print("Got IAC WILL MSP;  Sending IAC DONT MSP")
            conn.output(IAC + DONT + MSP)
        elif opt == ZMP:
            print("Got IAC WILL ZMP;  Sending IAC DONT ZMP")
            conn.output(IAC + DONT + ZMP)
        elif opt == GMCP:
            # TODO - support this eventually
            print("Got IAC WILL GMCP;  Sending IAC DONT GMCP")
            conn.output(IAC + DONT + GMCP)
        else:
            print("Got an *unknown* negotiation IAC WILL " + str(ord(opt)) + ", saying DONT")
            conn.output(IAC + DONT + opt)
    else:
        print("Got an *unknown* negotiation IAC WONT " + str(ord(opt)) + ", saying DONT")
        conn.output(IAC + DONT + opt)

def handle_iac_subnegotiation(sbdataq, conn):
    payload = deque(sbdataq)
    SB_ID = payload.popleft()
    if SB_ID == MSSP:
        handle_mssp(payload, conn)
    elif SB_ID == TTYPE:
        handle_ttype(payload, conn)
    else:
        print("unhandled IAC Subnegotiation")
        print(sbdataq)
    return

def handle_naws(conn):
    if conn.iac.get('NAWS') == True:
        cols = conn.output_pane.cols
        rows = conn.output_pane.rows
        # XXX TODO XXX -- chr(cols/rows) means this will gack if either is >= 256
        # The spec says 16-bit values supported but conn.output encodes to latin-1
        # which is actually sorta the problem.
        print("Sending IAC NAWS info:" + str(cols) + "x" + str(rows))
        conn.output(IAC + SB + NAWS + chr(cols) + chr(rows) + IAC + SE)
