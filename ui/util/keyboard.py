def get_mask(widget):
    display = widget.get_display()
    device_manager = display.get_device_manager()
    device = device_manager.get_client_pointer()
    # win is Gdk.Window, not Gtk
    win, x, y, mask = widget.get_window().get_device_position(device)
    return mask
