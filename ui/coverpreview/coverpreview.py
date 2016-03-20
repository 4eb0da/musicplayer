from gi.repository import Gtk, Gdk


class CoverPreview(Gtk.Dialog):
    def __init__(self, parent, title, pixbuf):
        Gtk.Dialog.__init__(self, title, None, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        window = parent.get_window()
        screen = parent.get_screen()
        monitor_num = screen.get_monitor_at_window(window)
        monitor = screen.get_monitor_workarea(monitor_num)

        self.set_border_width(6)
        # magic numbers
        self.set_default_size(min(pixbuf.get_width() + 20, monitor.width - 20), min(pixbuf.get_height() + 60, monitor.height - 20))

        scrolled_window = Gtk.ScrolledWindow.new(None, None)
        scrolled_window.set_property("vexpand", True)

        image = Gtk.Image()
        image.set_from_pixbuf(pixbuf)
        scrolled_window.add_with_viewport(image)

        box = self.get_content_area()
        box.add(scrolled_window)
        self.show_all()
