# https://specifications.freedesktop.org/mpris-spec/latest/
# https://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html


import dbus
import dbus.service
import os


class Mpris2(dbus.service.Object):
    BASE_IFACE = "org.mpris.MediaPlayer2"
    PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"

    def __init__(self, app):
        self.__app = app
        self.__current_track = None
        self.__metadata = None

        name = dbus.service.BusName("org.mpris.MediaPlayer2.musicplayer.instance" + str(os.getpid()),
                                    bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, name, "/org/mpris/MediaPlayer2")
        self.update_track()

        app.queue.connect("track", self.on_track)
        app.discoverer.connect("info", self.on_file_update)

    def update_track(self):
        track = self.__current_track
        title = track.name() if track else ""
        artist = ""
        album = ""

        if track and track.info:
            artist = track.info.artist
            album = track.info.album

        self.__metadata = dbus.Dictionary({
            "xesam:title": title or "Unknown",
            "xesam:artist": [artist or ""],
            "xesam:album": album or "",
        }, signature="sv", variant_level=1)

        self.PropertiesChanged(self.PLAYER_IFACE,
                               dbus.Dictionary({"Metadata": self.__metadata}, "sv", variant_level=1), [])

    def on_track(self, queue, track):
        self.__current_track = track
        self.update_track()

    def on_file_update(self, discoverer, pack):
        for track in pack:
            if self.__current_track == track:
                self.update_track()
                break

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        return self.GetAll(interface)[prop]

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ssv')
    def Set(self, interface, prop, value):
        pass

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface == self.BASE_IFACE:
            return {
                "DesktopEntry": "musicplayer"
            }

        elif interface == self.PLAYER_IFACE:
            return {
                "PlaybackStatus": "Playing",
                "Metadata": self.__metadata
            }

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, props):
        pass
