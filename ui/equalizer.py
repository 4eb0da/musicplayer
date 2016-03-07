from gi.repository import Gtk


class Equalizer(Gtk.VBox):
    def __init__(self, app):
        Gtk.VBox.__init__(self)

        self.app = app
        self.scales = []

        hbox = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        for i in range(0, 10):
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, -12, 12, 1)
            scale.set_data("index", i)
            scale.set_value(0)
            scale.set_inverted(True)
            scale.set_draw_value(False)
            scale.connect("value-changed", self.on_scale_change)
            hbox.pack_start(scale, True, True, 0)
            self.scales.append(scale)

        reset = Gtk.Button("_Reset", use_underline=True)
        reset.connect("clicked", self.on_reset)

        button_box = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.CENTER)
        button_box.pack_start(reset, True, True, 0)

        self.pack_start(hbox, True, True, 6)
        self.pack_start(button_box, False, False, 6)

        self.set_size_request(100, 150)

    def on_scale_change(self, scale):
        self.app.player.set_equalizer(scale.get_data("index"), scale.get_value())

    def on_reset(self, button):
        for scale in self.scales:
            scale.set_value(0)
