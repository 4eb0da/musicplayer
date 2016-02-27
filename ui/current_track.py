from gi.repository import Gtk, Pango

class CurrentTrack(Gtk.Box):
    def __init__(self, app):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.name = Gtk.Label("", xalign=0)
        self.name.set_ellipsize(Pango.EllipsizeMode.END)
        self.info = Gtk.Label("", xalign=0)
        self.info.set_ellipsize(Pango.EllipsizeMode.END)

        self.pack_start(self.name, False, False, 0)
        self.pack_start(self.info, False, False, 0)

        app.player.connect("play", self.on_track_change)
        app.discoverer.connect("info", self.on_file_update)

    def on_track_change(self, player, track):
        self.current_track = track
        self.update_title()

    def update_title(self):
        self.name.set_markup("<b>" + self.current_track.name() + "</b>")
        if self.current_track.info:
            self.info.set_text(self.current_track.info["ARTIST"][0] + " - " + self.current_track.info["ALBUM"][0])

    def on_file_update(self, discoverer, track):
        if self.current_track == track:
            self.update_title()
