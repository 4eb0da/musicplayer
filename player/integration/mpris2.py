# https://specifications.freedesktop.org/mpris-spec/latest/
# https://dbus.freedesktop.org/doc/dbus-python/doc/tutorial.html


import dbus
import dbus.service
import os
import tempfile
import random
import string


class Mpris2(dbus.service.Object):
    BASE_IFACE = "org.mpris.MediaPlayer2"
    PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"

    def __init__(self, app):
        self.__app = app
        self.__current_track = None
        self.__current_cover = None
        self.__temp_dir = tempfile.mkdtemp("musicplayer")
        self.__metadata = None
        self.__playback_status = "Stopped"
        self.__loop_status = "None"
        self.__shuffle = app.queue.shuffle
        self.__volume = 1

        self.__listeners = {}

        name = dbus.service.BusName("org.mpris.MediaPlayer2.musicplayer.instance" + str(os.getpid()),
                                    bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, name, "/org/mpris/MediaPlayer2")
        self.__update_track()

        app.queue.connect("play_pause", self.__on_play_pause)
        app.queue.connect("shuffle", self.__on_shuffle)
        app.queue.connect("repeat", self.__on_repeat)
        app.player.connect("volume_change", self.__on_volume_change)

    # i can't derive from GObject (because of metaclass conflict), so...
    def connect(self, name, listener):
        if name not in self.__listeners:
            self.__listeners[name] = []

        self.__listeners[name].append(listener)

    def emit(self, name):
        if name not in self.__listeners:
            return

        for listener in self.__listeners[name]:
            listener(self)

    def __update_track(self):
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
            "mpris:artUrl": self.__current_cover or "",
        }, signature="sv", variant_level=1)

        self.PropertiesChanged(self.PLAYER_IFACE,
                               dbus.Dictionary({
                                   "Metadata": self.__metadata,
                                   "CanPlay": bool(self.__current_track),
                                   "CanPause": bool(self.__current_track)
                               }, "sv", variant_level=1), [])

    def update_track(self, track, cover):
        self.__current_track = track
        if cover:
            path = str(self.__temp_dir) + "/" + ''.join(
                random.choice(string.ascii_lowercase) for i in range(10)) + ".jpg"
            cover.savev(path, "jpeg", [], [])
            self.__current_cover = "file://" + path
        else:
            self.__current_cover = None
        self.__update_track()

    def __on_play_pause(self, queue, play):
        self.__playback_status = "Playing" if play else "Paused"
        self.PropertiesChanged(self.PLAYER_IFACE,
                               dbus.Dictionary({"PlaybackStatus": self.__playback_status}, "sv", variant_level=1), [])

    def __on_shuffle(self, queue, shuffle):
        self.__shuffle = shuffle
        self.PropertiesChanged(self.PLAYER_IFACE,
                               dbus.Dictionary({"Shuffle": self.__shuffle}, "sv", variant_level=1), [])

    def __on_repeat(self, queue, repeat):
        self.__loop_status = "Playlist" if repeat else "None"
        self.PropertiesChanged(self.PLAYER_IFACE,
                               dbus.Dictionary({"LoopStatus": self.__loop_status}, "sv", variant_level=1), [])

    def __on_volume_change(self, player, volume, mute):
        if mute:
            volume = 0
        self.__volume = volume
        self.PropertiesChanged(self.PLAYER_IFACE,
                               dbus.Dictionary({"Volume": self.__volume}, "sv", variant_level=1), [])

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        return self.GetAll(interface)[prop]

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ssv')
    def Set(self, interface, prop, value):
        if prop == "PlaybackStatus":
            self.__app.queue.play_pause(True if value == "Playing" else False)
        elif prop == "LoopStatus":
            self.__app.queue.toggle_repeat(True if value == "Playlist" else False)
        elif prop == "Shuffle":
            self.__app.queue.toggle_shuffle(bool(value))
        elif prop == "Volume":
            self.__app.player.set_volume(float(value))

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface == self.BASE_IFACE:
            return {
                "DesktopEntry": "musicplayer"
            }

        elif interface == self.PLAYER_IFACE:
            return {
                "PlaybackStatus": self.__playback_status,
                "LoopStatus": self.__loop_status,
                "Metadata": self.__metadata,
                "Rate": 1,
                "MinimumRate": 1,
                "MaximumRate": 1,
                "Shuffle": self.__shuffle,
                "Volume": self.__volume,
                "CanGoNext": True,
                "CanGoPrevious": True,
                "CanPlay": bool(self.self.__current_track),
                "CanPause": bool(self.self.__current_track),
                "CanControl": True
            }

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, props):
        pass

    @dbus.service.method(PLAYER_IFACE)
    def Previous(self):
        self.__app.queue.previous()

    @dbus.service.method(PLAYER_IFACE)
    def Next(self):
        self.__app.queue.next()

    @dbus.service.method(PLAYER_IFACE)
    def Pause(self):
        self.__app.queue.play_pause(False)

    @dbus.service.method(PLAYER_IFACE)
    def PlayPause(self):
        self.__app.queue.play_pause()

    @dbus.service.method(PLAYER_IFACE)
    def Stop(self):
        self.__app.queue.play_pause(False)

    @dbus.service.method(PLAYER_IFACE)
    def Play(self):
        self.__app.queue.play_pause(True)

    @dbus.service.method(BASE_IFACE)
    def Raise(self):
        self.emit("raise")
