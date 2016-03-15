from gi.repository import Gtk, Gdk


class MenuToolButton(Gtk.ToggleToolButton):
    def __init__(self, popup):
        Gtk.ToggleToolButton.__init__(self)

        self.popup = popup

        self.connect("toggled", self.on_click)
        popup.connect("deactivate", lambda menu: self.set_active(False))

    def on_click(self, button):
        self.popup.popup(None, None, self.menu_position, button, Gdk.BUTTON_PRIMARY, Gtk.get_current_event_time())

    @staticmethod
    def menu_position(menu, button):
        menu_req, menu_req_pref = menu.get_preferred_size()
        window = button.get_window()
        pos, x, y = window.get_origin()
        allocation = button.get_allocation()
        x += allocation.x
        y += allocation.y
        screen = menu.get_screen()
        monitor_num = screen.get_monitor_at_window(window)
        monitor = screen.get_monitor_workarea(monitor_num)

        if y + allocation.height + menu_req.height < monitor.y + monitor.height:
            y += allocation.height
        elif y - menu_req.height >= monitor.y:
            y -= menu_req.height
        elif monitor.y + monitor.height - (y + allocation.height) > y:
            y += allocation.height
        else:
            y -= menu_req.height

        return x, y, False
