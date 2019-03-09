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
IAC     = bytes([255]) # "Interpret As Command"
DONT    = bytes([254])
DO      = bytes([253])
WONT    = bytes([252])
WILL    = bytes([251])
theNULL = bytes([0])

SE  = bytes([240])  # Subnegotiation End
NOP = bytes([241])  # No Operation
DM  = bytes([242])  # Data Mark
BRK = bytes([243])  # Break
IP  = bytes([244])  # Interrupt process
AO  = bytes([245])  # Abort output
AYT = bytes([246])  # Are You There
EC  = bytes([247])  # Erase Character
EL  = bytes([248])  # Erase Line
GA  = bytes([249])  # Go Ahead
SB  = bytes([250])  # Subnegotiation Begin

############# MU*-RELATED PROTOCOLS
ECHO        = bytes([1])  # echo
LINEMODE    = bytes([34]) # Linemode option
EOR         = bytes([25]) # end or record
NEW_ENVIRON = bytes([39]) # New - Environment variables

from filters.telnetiac.naws import handle_naws
NAWS     = bytes([31]) # window size

# MTTS - MUD Terminal Type Standard (https://tintin.sourceforge.io/protocols/mtts/)
#    (specific implementation of arpa Telnet IAC TTYPE command)
from filters.telnetiac.mtts import handle_mtts
MTTS = bytes([24]) # terminal type

# MSDP - MUD Server Data Protocol
MSDP = bytes([69])

# MSSP - MUD Server Status Protocol
from filters.telnetiac.mssp import handle_mssp
MSSP = bytes([70])

# MCCP - MUD Client Compression Protocol (http://www.gammon.com.au/mccp/protocol.html)
MCCP1 = bytes([85])
MCCP2 = bytes([86])

# MSP - Mud Sound Protocol (https://www.zuggsoft.com/zmud/msp.htm)
from window.mediainfo import msp_filter
MSP = bytes([90])

# MXP - MUD eXtension Protocol (https://www.zuggsoft.com/zmud/mxp.htm)
MXP = bytes([91])

# ZMP - Zenith MUD Protocol (http://discworld.starturtle.net/external/protocols/zmp.html)
ZMP = bytes([93])

# ATCP - Achaea Telnet Client Protocol (https://www.ironrealms.com/rapture/manual/files/FeatATCP-txt.html)
ATCP = bytes([200])

# GMCP - Generic MUD Communication Protocol (http://www.gammon.com.au/gmcp)
GMCP = bytes([201])


def process_line(conn, line):
    buf = [b'',b'']
    iacseq  = b''
    sbdataq = b''
    sb = 0
    option_callback = None

    # if we're compressing, decompress us back into a wad of bytes here.
    if 'MCCP' in conn.features:
        # TODO - try / except in case something breaks.
        # From the MCCP site:
        #
        # If any stream errors are seen on the decompressing side, they should
        # be treated as fatal errors, closing the connection. It is unlikely
        # that the compressing side will be transmitting useful information
        # after a compression error.

        # count up the bytes to update the status icon
        zbytes = len(line)
        line = conn.decompressor.decompress(line)
        ubytes = len(line)
        zbytes -= len(conn.decompressor.unused_data)

        conn.compressed_bytes   += zbytes
        conn.uncompressed_bytes += ubytes

        percent = 100 - round(conn.compressed_bytes * 100 / conn.uncompressed_bytes,1)

        conn.UpdateIcon('MCCP', f'MCCP enabled\n{conn.compressed_bytes} compressed bytes\n{conn.uncompressed_bytes} uncompressed bytes\n{percent}% compression')

        # Re-queue leftover compressed data
        conn.filter_queue = conn.decompressor.unused_data

    line = deque(line)
    while len(line):
        c = bytes([line.popleft()])
        if len(iacseq) == 0:
            if c == theNULL:
                continue
            # This was removing some stuff 8BitMUSH uses for art.  Why is this here?
            #if c == b"\021":
                #continue
            if c != IAC:
                buf[sb] += c
                continue
            else:
                iacseq += c
        elif len(iacseq) == 1:
            # 'IAC: IAC CMD [OPTION only for WILL/WONT/DO/DONT]'
            if c in (DO, DONT, WILL, WONT):
                iacseq += c
                continue
            iacseq = b''
            if c == IAC:
                buf[sb] = buf[sb] + c
            else:
                if c == SB: # SB ... SE start.
                    sb = 1
                    sbdataq = b''
                elif c == SE:
                    sb = 0
                    sbdataq = sbdataq + buf[1]
                    buf[1] = b''
                    result = handle_iac_subnegotiation(sbdataq, conn)
                    if result == "requeue":
                        print("Time to requeue!")
                        conn.filter_queue = line
                        return
        elif len(iacseq) == 2:
            cmd = bytes([iacseq[1]])
            iacseq = b''
            opt = c
            if cmd in (DO, DONT):
                handle_iac_do_negotiation(cmd, opt, conn)
            elif cmd in (WILL, WONT):
                handle_iac_will_negotiation(cmd, opt, conn)
    # end loop
    return buf[0]

def handle_iac_do_negotiation(cmd, opt, conn):
    if cmd == DO:
        if opt == MTTS:
            print("Got IAC DO MTTS;  Sending IAC WILL MTTS")
            conn.ActivateFeature('MTTS')
            conn.output(IAC + WILL + MTTS)
        elif opt == NEW_ENVIRON:
            print("Got IAC DO NEW_ENVIRON;  Sending IAC WONT NEW_ENVIRON")
            conn.output(IAC + WONT + NEW_ENVIRON)
        elif opt == NAWS:
            print("Got IAC DO NAWS; Sending IAC WILL NAWS + x/y info")
            conn.ActivateFeature('NAWS')
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
        if opt == MTTS:
            print("Got IAC DONT MTTS; Resetting and sending WONT MTTS")
            conn.mtts_reply = 0
            conn.output(IAC + WONT + MTTS)
        elif opt == NAWS:
            print("Got IAC DONT NAWS; Sending IAC WONT NAWS")
            conn.ActivateFeature('NAWS', False)
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
            conn.ActivateFeature('MSSP')
        elif opt == MCCP1 or opt == MCCP2:
            if 'MCCP' in conn.features:
                answer = DONT
                print("Got IAC WILL MCCP; Already compressing, Sending IAC DONT MCCP")
            else:
                answer = DO
                print("Got IAC WILL MCCP;  Sending IAC DO MCCP")
            conn.output(IAC + answer + opt)
        elif opt == MSP:
            print("Got IAC WILL MSP;  Sending IAC DO MSP")
            conn.output(IAC + DO + MSP)
            conn.ActivateFeature('MSP')
            conn.output_pane.register_filter('msp', msp_filter)
        elif opt == ZMP:
            print("Got IAC WILL ZMP;  Sending IAC DONT ZMP")
            conn.output(IAC + DONT + ZMP)
        elif opt == GMCP:
            # TODO - support this eventually
            print("Got IAC WILL GMCP;  Sending IAC DONT GMCP")
            conn.output(IAC + DONT + GMCP)
        elif opt == ECHO:
            print("Got IAC WILL ECHO")
            conn.do_echo = False
        else:
            print("Got an *unknown* negotiation IAC WILL " + str(ord(opt)) + ", saying DONT")
            conn.output(IAC + DONT + opt)
    elif cmd == WONT:
        if opt == ECHO:
            print("Got IAC WONT ECHO")
            conn.do_echo = True
        else:
            print("Got an *unknown* negotiation IAC WONT " + str(ord(opt)) + ", saying DONT")
            conn.output(IAC + DONT + opt)

def handle_iac_subnegotiation(sbdataq, conn):
    payload = deque(sbdataq)
    SB_ID = bytes([payload.popleft()])
    if SB_ID == MSSP:
        handle_mssp(payload, conn)
    elif SB_ID == MTTS:
        handle_mtts(payload, conn)
    elif SB_ID == MCCP1 or SB_ID == MCCP2:
        # Turn on the compression flag on the connection and requeue all remaning bytes
        conn.ActivateFeature('MCCP')
        conn.compressed_bytes = conn.uncompressed_bytes = 0
        return('requeue')
    else:
        print("unhandled IAC Subnegotiation")
        print(sbdataq)
    return


# Unimplemented / Unused / Uninteresting IAC protocols
#
# Telnet protocol options code (don't change)
# These ones all come from arpa/telnet.h
#BINARY         = bytes([0]) # 8-bit data path
#RCP            = bytes([2]) # prepare to reconnect
#SGA            = bytes([3]) # suppress go ahead
#NAMS           = bytes([4]) # approximate message size
#STATUS         = bytes([5]) # give status
#TM             = bytes([6]) # timing mark
#RCTE           = bytes([7]) # remote controlled transmission and echo
#NAOL           = bytes([8]) # negotiate about output line width
#NAOP           = bytes([9]) # negotiate about output page size
#NAOCRD         = bytes([10]) # negotiate about CR disposition
#NAOHTS         = bytes([11]) # negotiate about horizontal tabstops
#NAOHTD         = bytes([12]) # negotiate about horizontal tab disposition
#NAOFFD         = bytes([13]) # negotiate about formfeed disposition
#NAOVTS         = bytes([14]) # negotiate about vertical tab stops
#NAOVTD         = bytes([15]) # negotiate about vertical tab disposition
#NAOLFD         = bytes([16]) # negotiate about output LF disposition
#XASCII         = bytes([17]) # extended ascii character set
#LOGOUT         = bytes([18]) # force logout
#BM             = bytes([19]) # byte macro
#DET            = bytes([20]) # data entry terminal
#SUPDUP         = bytes([21]) # supdup protocol
#SUPDUPOUTPUT   = bytes([22]) # supdup output
#SNDLOC         = bytes([23]) # send location
#TUID           = bytes([26]) # TACACS user identification
#OUTMRK         = bytes([27]) # output marking
#TTYLOC         = bytes([28]) # terminal location number
#VT3270REGIME   = bytes([29]) # 3270 regime
#X3PAD          = bytes([30]) # X.3 PAD
#TSPEED         = bytes([32]) # terminal speed
#LFLOW          = bytes([33]) # remote flow control
#XDISPLOC       = bytes([35]) # X Display Location
#OLD_ENVIRON    = bytes([36]) # Old - Environment variables
#AUTHENTICATION = bytes([37]) # Authenticate
#ENCRYPT        = bytes([38]) # Encryption option

# the following ones come from
# http://www.iana.org/assignments/telnet-options
# Unfortunately, that document does not assign identifiers
# to all of them, so we are making them up
#TN3270E             = bytes([40]) # TN3270E
#XAUTH               = bytes([41]) # XAUTH
#CHARSET             = bytes([42]) # CHARSET
#RSP                 = bytes([43]) # Telnet Remote Serial Port
#COM_PORT_OPTION     = bytes([44]) # Com Port Control Option
#SUPPRESS_LOCAL_ECHO = bytes([45]) # Telnet Suppress Local Echo
#TLS                 = bytes([46]) # Telnet Start TLS
#KERMIT              = bytes([47]) # KERMIT
#SEND_URL            = bytes([48]) # SEND-URL
#FORWARD_X           = bytes([49]) # FORWARD_X

#PRAGMA_LOGON     = bytes([138]) # TELOPT PRAGMA LOGON
#SSPI_LOGON       = bytes([139]) # TELOPT SSPI LOGON
#PRAGMA_HEARTBEAT = bytes([140]) # TELOPT PRAGMA HEARTBEAT
#EXOPL            = bytes([255]) # Extended-Options-List
#NOOPT            = bytes([0])

