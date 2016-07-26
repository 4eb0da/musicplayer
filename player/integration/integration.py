from .mpris2 import Mpris2
from .gnome_keys import GnomeKeys
from .notifications import Notifications
from .unity import UnityQuickList

from gi.repository import GObject, GdkPixbuf


class Integration(GObject.Object):
    MAX_IMAGE_SIZE = 120

    __gsignals__ = {
        'raise': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, app):
        GObject.Object.__init__(self)

        self.__current_track = None
        self.__current_cover = None

        self.__mpris = Mpris2(app)
        self.__gnome_keys = GnomeKeys(app)
        self.__notifications = Notifications(app)
        self.__unity_quick_list = UnityQuickList(app)

        self.__mpris.connect("raise", lambda mpris: self.emit("raise"))

        app.queue.connect("track", self.__on_track)
        app.discoverer.connect("info", self.__on_file_update)
        app.player.connect("cover", self.__on_cover)

    def toggle_focused(self, focused):
        self.__notifications.toggle_focused(focused)

    def cleanup(self):
        self.__mpris.cleanup()

    def __on_track(self, queue, track):
        self.__current_track = track
        self.__current_cover = None
        self.__update_track()

    def __update_track(self):
        self.__mpris.update_track(self.__current_track, self.__current_cover)
        self.__notifications.update_track(self.__current_track, self.__current_cover)

    def __on_file_update(self, discoverer, pack):
        for track in pack:
            if self.__current_track == track:
                self.__update_track()
                return

    def __on_cover(self, player, cover):
        self.__current_cover = self.__scale_pixbuf(cover)
        self.__update_track()

    def __scale_pixbuf(self, pixbuf):
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        size = max(width, height)

        if size > self.MAX_IMAGE_SIZE:
            scale = self.MAX_IMAGE_SIZE / size
            scaled_width = width * scale
            scaled_height = height * scale
            pixbuf = pixbuf.scale_simple(scaled_width, scaled_height, GdkPixbuf.InterpType.HYPER)

        return pixbuf
