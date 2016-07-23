from .mpris2 import Mpris2
from .gnome_keys import GnomeKeys
from .notifications import Notifications

from gi.repository import GObject


class Integration(GObject.Object):
    __gsignals__ = {
        'raise': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self, app):
        GObject.Object.__init__(self)

        self.__mpris = Mpris2(app)
        self.__gnome_keys = GnomeKeys(app)
        self.__notifications = Notifications(app)

        self.__mpris.connect("raise", lambda mpris: self.emit("raise"))

    def toggle_focused(self, focused):
        self.__notifications.toggle_focused(focused)
