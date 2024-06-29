import wx

MSSP_VAR = chr(1)
MSSP_VAL = chr(2)

def handle_mssp(payload, conn):
    bucket = ''
    extracted = {}
    current_var = ''
    while payload:
        c = chr(payload.popleft())
        if (c == MSSP_VAR) or (c == MSSP_VAL):
            if c == MSSP_VAR:
                if bucket:
                    if current_var:
                        extracted[current_var].append(bucket)
                current_var = ''
            if c == MSSP_VAL:
                if current_var:
                    extracted[current_var].append(bucket)
                else:
                    extracted[bucket] = []
                    current_var = bucket
            bucket = ''
        else:
            bucket = bucket + c
    if bucket: extracted[current_var].append(bucket)

    # OK, let's mash that all back into the current world

    # TODO - explicitly examine each of the official MSSP variables
    # https://tintin.sourceforge.io/protocols/mssp/
    # and treat each piece of info appropriately, ie, mash into our scheme,
    # or possibly just add each of them to our scheme.

    world = conn.world

    got_new_info = []
    for key in extracted:
        if conn.mssp_info:
            conn.mssp_info.add_message({str(key) : str(extracted[key])})
        worldkey = "MSSP_" + key.capitalize()
        if not str(world.get(worldkey)) == str(extracted[key]):
            wx.LogMessage(f"Got new MSSP info: {worldkey} = {extracted[key]} (Was: {world.get(worldkey)})")
            got_new_info.append(key)

    # XXX temporarily stopping the dialog / save madness
    return

    if got_new_info:
        message = "Got new MSSP info for this world:\n\n"
        for key in got_new_info:
            worldkey = "MSSP_" + key.capitalize()
            message = message + key + ":" + str(extracted[key]) + "\n"
        message = message + "\nSave new info into world?"
        dlg = wx.MessageDialog(conn, message, "New World Info", wx.YES_NO)
        dlg.SetYesNoLabels(wx.ID_SAVE, "&Don't Save")
        if dlg.ShowModal() == wx.ID_YES:
            for key in extracted:
                worldkey = "MSSP_" + key.capitalize()
                world[worldkey] = extracted[key]
            world.save()

    return
