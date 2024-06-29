import wx

MSSP_VAR = chr(1)
MSSP_VAL = chr(2)

# TODO - we only store the last value of a multi-value variable.
# According to the spec, the last one should be the default / preferred
# one, but this is still suboptimal.  This is because we don't have a
# sane way to store list values in the worlds .ini-format file.
# TODO - maybe worlds wants to be a json file.
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
                        extracted[current_var] = bucket
                current_var = ''
            elif c == MSSP_VAL:
                if current_var:
                    extracted[current_var] = bucket
                else:
                    extracted[bucket] = ''
                    current_var = bucket
            bucket = ''
        else:
            bucket = bucket + c
    if bucket: extracted[current_var] = bucket

    # OK, let's mash that all back into the current world

    world = conn.world

    # First, check if any of it is new.
    got_new_info = []
    for key, value in extracted.items():
        if conn.mssp_info:
            conn.mssp_info.add_message({str(key) : str(value)})
        worldkey = "MSSP_" + key.capitalize()
        if not str(world.get(worldkey)) == str(value):
            wx.LogMessage(f"Got new MSSP info: {worldkey} = {value} (Was: {world.get(worldkey)})")
            got_new_info.append(key)

    # TODO - explicitly examine each of the official MSSP variables
    # https://tintin.mudhalla.net/protocols/mssp/
    # and treat each piece of info appropriately, ie, mash into our scheme,
    # or possibly just add each of them to our scheme.

    if got_new_info:
#        message = "Got new MSSP info for this world:\n\n"
#        for key in got_new_info:
#            worldkey = "MSSP_" + key.capitalize()
#            message = message + key + ":" + str(extracted[key]) + "\n"

#        message = message + "\nSave new world info?"
#        dlg = wx.MessageDialog(conn, message, "New World Info", wx.YES_NO)
#        dlg.SetYesNoLabels(wx.ID_SAVE, "&Don't Save")
#        if dlg.ShowModal() == wx.ID_YES:
            for key in got_new_info:
                worldkey = "MSSP_" + key.upper()
                world[worldkey] = extracted[key]
            world.save()
