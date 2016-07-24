from gi.repository import Notify, GdkPixbuf


class Notifications:
    APP_NAME = "musicplayer"

    def __init__(self, app):
        self.__focused = False
        self.__current_track = None
        self.__current_cover = None
        self.__notification = None

        Notify.init(self.APP_NAME)

    def toggle_focused(self, focused):
        self.__focused = focused

    def update_track(self, track, cover):
        self.__current_track = track
        self.__current_cover = cover
        self.__update_track()

    def __update_track(self):
        if self.__focused:
            return

        if not self.__notification:
            self.__notification = Notify.Notification.new("", "", "")

        self.__notification.update(self.__current_track.name(), self.__current_track.info.album if self.__current_track.info else "", "")

        if self.__current_cover:
            self.__notification.set_image_from_pixbuf(self.__current_cover)

        self.__notification.show()
