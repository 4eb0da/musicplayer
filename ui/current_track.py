from gi.repository import Gtk, Pango, GObject

class CurrentTrack(Gtk.Box):
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.app = app
        self.current_track = None
        self.seek_delay = None
        self.name = Gtk.Label("", xalign=0)
        self.name.set_ellipsize(Pango.EllipsizeMode.END)
        self.info = Gtk.Label("", xalign=0)
        self.info.set_ellipsize(Pango.EllipsizeMode.END)
        self.time = Gtk.Label("0:00 / 0:00", xalign=0)
        self.scale_pressed = False
        self.scale = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, None)
        self.scale.set_draw_value(False)

        self.scale_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.scale_box.pack_start(self.time, False, False, 0)
        self.scale_box.pack_start(self.scale, True, True, 0)

        self.pack_start(self.name, False, False, 0)
        self.pack_start(self.info, False, False, 0)
        self.pack_start(self.scale_box, False, False, 0)

        app.player.connect("play", self.on_track_change)
        app.discoverer.connect("info", self.on_file_update)
        self.scale.connect("button-press-event", self.on_scale_press)
        self.scale.connect("button-release-event", self.on_scale_release)
        self.scale.connect("change-value", self.on_scale_move)

        GObject.timeout_add(500, self.update_scale)

    def on_track_change(self, player, track):
        self.current_track = track
        self.scale.set_value(0)
        self.scale.set_range(0, 60000)
        self.update_title()

    def update_title(self):
        self.name.set_markup("<b>" + self.current_track.name() + "</b>")
        if self.current_track.info:
            self.info.set_text(self.current_track.info["ARTIST"][0] + " - " + self.current_track.info["ALBUM"][0])

    def on_file_update(self, discoverer, track):
        if self.current_track == track:
            self.update_title()

    def update_scale(self, position = None):
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

    def on_scale_release(self, widget, event):
        self.scale_pressed = False
        self.seek(event.x / self.scale.get_allocated_width() * self.app.player.get_duration(), False)

    def on_scale_move(self, widget, scroll, value):
        self.seek(value)

    def seek(self, pos, delay = True):
        if self.seek_delay is not None:
            GObject.source_remove(self.seek_delay)
            self.seek_delay = None
        if delay:
            self.seek_delay = GObject.timeout_add(50, lambda: self.app.player.set_position(pos))
        else:
            self.app.player.set_position(pos)
        self.update_scale(pos)
