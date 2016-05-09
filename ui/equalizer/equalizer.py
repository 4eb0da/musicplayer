from gi.repository import Gtk
import os


class Equalizer(Gtk.VBox):
    def __init__(self, app):
        Gtk.VBox.__init__(self)

        self.app = app
        self.scales = []

        self.preset_store = Gtk.ListStore(str)

        renderer_text = Gtk.CellRendererText()
        self.preset_combo = Gtk.ComboBox.new_with_model(self.preset_store)
        self.preset_combo.pack_start(renderer_text, True)
        self.preset_combo.add_attribute(renderer_text, "text", 0)
        self.preset_combo.connect("changed", self.on_preset_change)

        edit_image = Gtk.Image.new_from_stock(Gtk.STOCK_EDIT, Gtk.IconSize.BUTTON)
        self.rename = Gtk.Button(None)
        self.rename.set_image(edit_image)
        self.rename.set_tooltip_text("Edit name")
        self.rename.set_sensitive(False)
        self.rename.connect("clicked", self.on_rename)

        top_box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        top_box.pack_start(self.preset_combo, True, True, 6)
        top_box.pack_start(self.rename, False, False, 6)

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

        add = Gtk.Button("_Add", use_underline=True)
        add.connect("clicked", self.on_add)
        self.remove = Gtk.Button("Remove")
        self.remove.connect("clicked", self.on_remove)

        button_box = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.CENTER)
        button_box.set_property("spacing", 6)
        button_box.pack_start(add, True, True, 0)
        button_box.pack_start(self.remove, True, True, 0)
        button_box.pack_start(reset, True, True, 0)

        self.pack_start(top_box, False, False, 6)
        self.pack_start(hbox, True, True, 6)
        self.pack_start(button_box, False, False, 6)

        self.set_size_request(100, 200)

        self.__update_combo()
        self.__update_preset()

    def __get_active_preset_name(self):
        return self.app.equalizer.get_presets()[self.preset_combo.get_active()]

    def on_scale_change(self, scale):
        self.app.equalizer.set_preset_val(
            self.__get_active_preset_name(),
            scale.get_data("index"),
            int(scale.get_value())
        )

    def on_reset(self, button):
        self.app.equalizer.reset_preset(self.__get_active_preset_name())
        self.__update_preset()

    def __update_combo(self):
        active_preset = self.app.equalizer.get_active_preset()
        active_preset_index = 0
        self.preset_store.clear()

        for index, preset in enumerate(self.app.equalizer.get_presets()):
            self.preset_store.append([preset])
            if preset == active_preset["name"]:
                active_preset_index = index
        self.preset_combo.set_active(active_preset_index)

    def __update_preset(self):
        preset = self.app.equalizer.get_active_preset()
        for i in range(0, 10):
            self.scales[i].set_value(preset["vals"][i])

        self.remove.set_sensitive(not preset["default"])
        self.rename.set_sensitive(not preset["default"])

    def on_preset_change(self, combo):
        self.app.equalizer.set_preset(self.__get_active_preset_name())
        self.__update_preset()

    def on_add(self, button):
        name = self.__run_dialog()
        if name:
            self.app.equalizer.add_preset(name)
            self.app.equalizer.set_preset(name)

            self.__update_combo()
            self.__update_preset()

    def __run_dialog(self, name=None):
        new_name = name

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "preset_name.glade"))
        dialog = builder.get_object("dialog")
        entry = builder.get_object("name")

        if name:
            entry.set_text(name)
            dialog.set_title("Rename preset")
        else:
            dialog.set_title("Add preset")

        if dialog.run() == Gtk.ResponseType.OK:
            new_name = entry.get_text()

        dialog.destroy()

        return new_name

    def on_rename(self, button):
        name = self.__get_active_preset_name()
        new_name = self.__run_dialog(name)
        if new_name != name:
            self.app.equalizer.rename_preset(name, new_name)
            self.__update_combo()

    def on_remove(self, button):
        name = self.__get_active_preset_name()
        self.app.equalizer.remove_preset(name)

        self.__update_combo()
        self.__update_preset()
