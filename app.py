import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib
import sys

from ui.main_window import MainWindow


class MusicPlayerApplication(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)
        GLib.set_application_name('MusicPlayer')
        self.win = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.win = MainWindow(self)

    def do_activate(self):
        self.win.show_all()


app = MusicPlayerApplication()
exit_status = app.run(sys.argv)
sys.exit(exit_status)