import wx

IAC  = bytes([255]) # "Interpret As Command"
SE   = bytes([240])  # Subnegotiation End
SB   = bytes([250])  # Subnegotiation Begin
NAWS = bytes([31]) # window size

def handle_naws(conn):
    if 'NAWS' in conn.features:
        cols = conn.output_pane.cols
        rows = conn.output_pane.rows
        # Someday in the 45th century someone will be running this antique code on
        # a millon x million character terminal of some kind.  Anyway we're allowed 16 bits
        if cols > 65535: cols = 65535
        if rows > 65535: rows = 65535
        c1, c2 = divmod(cols, 256)
        colsbytes = bytes([c1]) + bytes([c2])
        r1, r2 = divmod(rows, 256)
        rowsbytes = bytes([r1]) + bytes([r2])

        # if we have a 255, IAC requires we send it twice
        if c1 == 255: colsbytes = bytes([c1]) + colsbytes
        if c2 == 255: colsbytes = colsbytes + bytes([c2])
        if r1 == 255: rowsbytes = bytes([r1]) + rowsbytes
        if r2 == 255: rowsbytes = rowsbytes + bytes([r2])

        wx.LogMessage(f"Sending IAC NAWS info: {c1} {c2} x {r1} {r2}")
        conn.output(IAC + SB + NAWS + colsbytes + rowsbytes + IAC + SE)

        conn.UpdateIcon('NAWS', f'NAWS enabled: {cols}x{rows}')
