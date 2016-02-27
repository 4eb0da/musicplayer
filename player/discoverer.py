import taglib
import gi

gi.require_version("Gtk", "3.0")

from threading import Thread, Condition
from gi.repository import Gtk, GObject


class Discoverer(GObject.Object):
    __gsignals__ = {
        'info': (GObject.SIGNAL_RUN_FIRST, None, (object,))
    }

    def __init__(self):
        GObject.Object.__init__(self)

        self.queue = []
        self.condition = Condition()
        self.thread = Thread(target=self.discover, args=())
        self.thread.daemon = True
        self.thread.start()

    def discover(self):
        while True:
            with self.condition:
                if not(len(self.queue)):
                    self.condition.wait()
                items = [track for track in self.queue if not track.info]
                self.queue = []
            for track in items:
                track.info = taglib.File(track.fullpath).tags
                GObject.idle_add(self.emit, "info", track)

    def add(self, tracks):
        with self.condition:
            self.queue += tracks
            self.condition.notify()
