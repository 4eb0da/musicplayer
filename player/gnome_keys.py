# https://gist.github.com/davidjb/e6cee3a040b1532e728d

import dbus


class GnomeKeys:
    APP_NAME = "musicplayer"
    OBJECT_NAME = "org.gnome.SettingsDaemon"
    OBJECT_PATH = "/org/gnome/SettingsDaemon/MediaKeys"
    IFACE_NAME = "org.gnome.SettingsDaemon.MediaKeys"
    SIGNAL_NAME = "MediaPlayerKeyPressed"

    def __init__(self, app):
        self.__app = app
        bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
        bus_object = bus.get_object(self.OBJECT_NAME, self.OBJECT_PATH)

        bus_object.GrabMediaPlayerKeys(self.APP_NAME, 0, dbus_interface=self.IFACE_NAME)
        bus_object.connect_to_signal(self.SIGNAL_NAME, self.__on_mediakey)
        bus_object.GrabMediaPlayerKeys(self.APP_NAME, 0, dbus_interface=self.IFACE_NAME)

    def __on_mediakey(self, application, *mmkeys):
        if application != self.APP_NAME:
            return

        for key in mmkeys:
            if key == "Play" or key == "Stop":
                self.__app.queue.play_pause()
            elif key == "Next":
                self.__app.queue.next()
            elif key == "Previous":
                self.__app.queue.previous()
