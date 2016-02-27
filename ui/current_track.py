from gi.repository import Gtk, Pango, GObject

class CurrentTrack(Gtk.Box):
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.current_track = None
        self.name = Gtk.Label("", xalign=0)
        self.name.set_ellipsize(Pango.EllipsizeMode.END)
        self.info = Gtk.Label("", xalign=0)
        self.info.set_ellipsize(Pango.EllipsizeMode.END)
        self.scale = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, None)
        self.scale.set_draw_value(False)

        self.pack_start(self.name, False, False, 0)
        self.pack_start(self.info, False, False, 0)
        self.pack_start(self.scale, False, False, 0)

        app.player.connect("play", self.on_track_change)
        app.discoverer.connect("info", self.on_file_update)

        GObject.timeout_add(500, self.update_track)

    def on_track_change(self, player, track):
        self.current_track = track
        self.scale.set_value(0)
        self.update_title()

    def update_title(self):
        self.name.set_markup("<b>" + self.current_track.name() + "</b>")
        if self.current_track.info:
            self.info.set_text(self.current_track.info["ARTIST"][0] + " - " + self.current_track.info["ALBUM"][0])

    def on_file_update(self, discoverer, track):
        if self.current_track == track:
            self.update_title()

    def update_track(self):
        if self.current_track:
            self.scale.set_range(0, self.app.player.get_duration())
            self.scale.set_value(self.app.player.get_position())
        GObject.timeout_add(500, self.update_track)
