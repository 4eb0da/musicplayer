from gi.repository import Notify, GdkPixbuf


class Notifications:
    APP_NAME = "musicplayer"
    MAX_IMAGE_SIZE = 120

    def __init__(self, app):
        self.__focused = False
        self.__current_track = None
        self.__current_ccover = None
        self.__notification = None

        Notify.init(self.APP_NAME)

        app.queue.connect("track", self.__on_track)
        app.discoverer.connect("info", self.__on_file_update)
        app.player.connect("cover", self.__on_cover)

    def toggle_focused(self, focused):
        self.__focused = focused

    def __on_track(self, queue, track):
        self.__current_track = track
        self.__current_cover = None
        self.__update_track()

    def __on_file_update(self, discoverer, pack):
        for track in pack:
            if self.__current_track == track:
                self.__update_track()
                return

    def __on_cover(self, player, cover):
        self.__current_cover = self.__scale_pixbuf(cover)
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
