#!/usr/bin/python3

import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Gst, GObject
from dbus.mainloop.glib import DBusGMainLoop
import sys

from ui.main_window import MainWindow

from player.player import Player
from player.queue import Queue
from player.discoverer import Discoverer
from player.settings import Settings
from player.equalizer import Equalizer
from player.mpris2 import Mpris2
from player.gnome_keys import GnomeKeys

GObject.threads_init()
Gst.init("")
DBusGMainLoop(set_as_default=True)


class MusicPlayerApplication(Gtk.Application):
    APP_NAME = "MusicPlayer"
    APP_CONFIG_PATH = "musicplayer"

    def __init__(self):
        Gtk.Application.__init__(self)
        GLib.set_application_name(self.APP_NAME)
        self.win = None
        self.settings = None
        self.discoverer = None
        self.player = None
        self.equalizer = None
        self.queue = None
        self.mpris2 = None
        self.gnome_keys = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.settings = Settings(self)
        self.discoverer = Discoverer()
        self.player = Player(self)
        self.equalizer = Equalizer(self)
        self.queue = Queue(self)
        self.mpris2 = Mpris2(self)
        self.gnome_keys = GnomeKeys(self)

        self.win = MainWindow(self)

    def do_activate(self):
        self.win.show_all()


app = MusicPlayerApplication()
exit_status = app.run(sys.argv)
sys.exit(exit_status)
