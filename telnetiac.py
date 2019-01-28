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
#BINARY = chr(0) # 8-bit data path
#ECHO = chr(1) # echo
#RCP = chr(2) # prepare to reconnect
#SGA = chr(3) # suppress go ahead
#NAMS = chr(4) # approximate message size
#STATUS = chr(5) # give status
#TM = chr(6) # timing mark
#RCTE = chr(7) # remote controlled transmission and echo
#NAOL = chr(8) # negotiate about output line width
#NAOP = chr(9) # negotiate about output page size
#NAOCRD = chr(10) # negotiate about CR disposition
#NAOHTS = chr(11) # negotiate about horizontal tabstops
#NAOHTD = chr(12) # negotiate about horizontal tab disposition
#NAOFFD = chr(13) # negotiate about formfeed disposition
#NAOVTS = chr(14) # negotiate about vertical tab stops
#NAOVTD = chr(15) # negotiate about vertical tab disposition
#NAOLFD = chr(16) # negotiate about output LF disposition
#XASCII = chr(17) # extended ascii character set
#LOGOUT = chr(18) # force logout
#BM = chr(19) # byte macro
#DET = chr(20) # data entry terminal
#SUPDUP = chr(21) # supdup protocol
#SUPDUPOUTPUT = chr(22) # supdup output
#SNDLOC = chr(23) # send location
#TTYPE = chr(24) # terminal type
#EOR = chr(25) # end or record
#TUID = chr(26) # TACACS user identification
#OUTMRK = chr(27) # output marking
#TTYLOC = chr(28) # terminal location number
#VT3270REGIME = chr(29) # 3270 regime
#X3PAD = chr(30) # X.3 PAD
#NAWS = chr(31) # window size
#TSPEED = chr(32) # terminal speed
#LFLOW = chr(33) # remote flow control
#LINEMODE = chr(34) # Linemode option
#XDISPLOC = chr(35) # X Display Location
#OLD_ENVIRON = chr(36) # Old - Environment variables
#AUTHENTICATION = chr(37) # Authenticate
#ENCRYPT = chr(38) # Encryption option
#NEW_ENVIRON = chr(39) # New - Environment variables
## the following ones come from
## http://www.iana.org/assignments/telnet-options
## Unfortunately, that document does not assign identifiers
## to all of them, so we are making them up
#TN3270E = chr(40) # TN3270E
#XAUTH = chr(41) # XAUTH
#CHARSET = chr(42) # CHARSET
#RSP = chr(43) # Telnet Remote Serial Port
#COM_PORT_OPTION = chr(44) # Com Port Control Option
#SUPPRESS_LOCAL_ECHO = chr(45) # Telnet Suppress Local Echo
#TLS = chr(46) # Telnet Start TLS
#KERMIT = chr(47) # KERMIT
#SEND_URL = chr(48) # SEND-URL
#FORWARD_X = chr(49) # FORWARD_X
#PRAGMA_LOGON = chr(138) # TELOPT PRAGMA LOGON
#SSPI_LOGON = chr(139) # TELOPT SSPI LOGON
#PRAGMA_HEARTBEAT = chr(140) # TELOPT PRAGMA HEARTBEAT
#EXOPL = chr(255) # Extended-Options-List
#NOOPT = chr(0)


# MSSP - MUD Server Status Protocol
MSSP     = chr(70)
MSSP_VAR = chr(1)
MSSP_VAL = chr(2)

# GMCP - Generic MUD Communication Protocol
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
                print('IAC ', cmd == DO and 'DO' or 'DONT', ord(opt))
            elif cmd in (WILL, WONT):
                print('IAC ', cmd == WILL and 'WILL' or 'WONT', ord(opt))
                handle_iac_negotiation(opt, conn)
    # end loop
    return buf[0]

def handle_iac_negotiation(opt, conn):
    if opt == MSSP:
        print("Sending IAC DO MSSP")
        conn.output(IAC + DO + MSSP)
    elif opt == GMCP:
        # TODO - support this eventually
        print("Sending IAC DONT GMCP")
        conn.output(IAC + DONT + GMCP)
    else:
        print("Got an unknown IAC negotiation, saying no")
        conn.output(IAC + DONT + opt)
    return

def handle_iac_subnegotiation(sbdataq, conn):
    payload = deque(sbdataq)
    SB_ID = payload.popleft()
    if SB_ID == MSSP:
        handle_mssp(payload, conn)
    else:
        print("Unknown IAC Subnegotiation")
        print(sbdataq)
    return

def handle_mssp(payload, conn):
    getting_var = 0
    getting_val = 0
    bucket = ''
    extracted = {}
    current_var = ''
    while payload:
        c = payload.popleft()
        if (c == MSSP_VAR) or (c == MSSP_VAL):
            if c == MSSP_VAR:
                getting_var = 1
                if bucket:
                    if current_var:
                        extracted[current_var].append(bucket)
                getting_val = 0
                current_var = ''
            if c == MSSP_VAL:
                getting_val = 1
                if current_var:
                    extracted[current_var].append(bucket)
                else:
                    extracted[bucket] = []
                    current_var = bucket
                getting_var = 0
            bucket = ''
        else:
            bucket = bucket + c
    if bucket: extracted[current_var].append(bucket)

    # OK, let's mash that all back into the current world
    world = conn.world

    for key in extracted:
        worldkey = "MSSP_" + key.capitalize()
        world[worldkey] = extracted[key]

    # TODO - don't start filling up the worlds file with "new connection"
    # just because some random server returned some MSSP
    #
    # TODO - probably prompt to save in this case?  This is where we start to
    # mash the MSSP info into the world instead of off to the MSSP_Side.
    if not world['name'] == "New Connection":
        world.save()

    return

