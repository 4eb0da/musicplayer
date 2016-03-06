from gi.repository import Gtk


class Equalizer(Gtk.HBox):
    def __init__(self, app):
        Gtk.HBox.__init__(self)

        self.app = app

        for i in range(0, 10):
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, -12, 12, 1)
            scale.set_data("index", i)
            scale.set_value(0)
            scale.set_inverted(True)
            scale.set_draw_value(False)
            scale.connect("value-changed", self.on_scale_change)
            self.pack_start(scale, True, True, 0)

        self.set_size_request(100, 150)

    def on_scale_change(self, scale):
        self.app.player.set_equalizer(scale.get_data("index"), scale.get_value())
