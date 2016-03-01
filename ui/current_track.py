from gi.repository import Gtk, Pango, GObject, GdkPixbuf


class CurrentTrack(Gtk.Box):
    MAX_IMAGE_SIZE = 40
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.app = app
        self.current_track = None
        self.seek_delay = None
        self.name = Gtk.Label("", xalign=0)
        self.name.set_ellipsize(Pango.EllipsizeMode.END)
        self.info = Gtk.Label("", xalign=0)
        self.info.set_ellipsize(Pango.EllipsizeMode.END)
        self.cover = Gtk.Image()
        self.time = Gtk.Label("0:00 / 0:00", xalign=0)
        self.scale_pressed = False
        self.scale = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, None)
        self.scale.set_draw_value(False)
        self.volume = Gtk.VolumeButton.new()
        self.volume.set_value(100)

        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.info_box.pack_start(self.name, False, False, 0)
        self.info_box.pack_start(self.info, False, False, 0)

        self.top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.top_box.pack_start(self.info_box, True, True, 0)
        self.top_box.pack_start(self.cover, False, False, 0)

        self.scale_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.scale_box.pack_start(self.time, False, False, 0)
        self.scale_box.pack_start(self.scale, True, True, 0)
        self.scale_box.pack_start(self.volume, False, False, 0)

        self.pack_start(self.top_box, False, False, 0)
        self.pack_start(self.scale_box, False, False, 0)

        app.player.connect("play", self.on_track_change)
        app.player.connect("cover", self.on_cover)
        app.discoverer.connect("info", self.on_file_update)
        self.scale.connect("button-press-event", self.on_scale_press)
        self.scale.connect("button-release-event", self.on_scale_release)
        self.scale.connect("change-value", self.on_scale_move)
        self.volume.connect("value-changed", self.on_volume_change)

        GObject.timeout_add(500, self.update_scale)

    def scale_pixbuf(self, pixbuf):
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        size = max(width, height)

        if size > self.MAX_IMAGE_SIZE:
            scale = self.MAX_IMAGE_SIZE / size
            scaled_width = width * scale
            scaled_height = height * scale
            pixbuf = pixbuf.scale_simple(scaled_width, scaled_height, GdkPixbuf.InterpType.HYPER)

        return pixbuf

    def on_track_change(self, player, track):
        self.current_track = track
        self.scale.set_value(0)
        self.scale.set_range(0, 60000)
        self.update_title()
        self.cover.hide()

    def update_title(self):
        self.name.set_markup("<b>" + self.current_track.name() + "</b>")
        if self.current_track.info:
            self.info.set_text(self.current_track.info.artist + " — " + self.current_track.info.album)

    def on_file_update(self, discoverer, track):
        if self.current_track == track:
            self.update_title()

    def update_scale(self, position=None):
        if self.current_track:
            duration = self.app.player.get_duration()
            if position is None:
                position = self.app.player.get_position()
            self.time.set_text(self.format_time(position) + " / " + self.format_time(duration))
            if not self.scale_pressed:
                self.scale.set_range(0, duration)
                self.scale.set_value(position)
        return True

    def format_time(self, time):
        time = int(time / 1000)
        mins = time // 60
        secs = time % 60
        if secs < 10:
            secs = "0" + str(secs)
        return str(mins) + ":" + str(secs)

    def on_scale_press(self, widget, event):
        self.scale_pressed = True
        self.app.queue.toggle_change(False)

    def on_scale_release(self, widget, event):
        self.seek(event.x / self.scale.get_allocated_width() * self.app.player.get_duration())
        self.scale_pressed = False
        self.app.queue.toggle_change(True)

    def on_scale_move(self, widget, scroll, value):
        self.seek(value)

    def seek(self, pos):
        if self.seek_delay is not None:
            GObject.source_remove(self.seek_delay)
        self.seek_delay = GObject.timeout_add(50, lambda: self.app.player.set_position(pos))
        self.update_scale(pos)

    def on_volume_change(self, scale, value):
        self.app.player.set_volume(value)

    def on_cover(self, player, cover):
        self.cover.set_from_pixbuf(self.scale_pixbuf(cover))
        self.cover.show()
