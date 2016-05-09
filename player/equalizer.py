import copy

PRESETS = [{
    "name": "Default",
    "default_vals": [
        0, 0, 0, 0, 0,
        0, 0, 0, 0, 0
    ]
}, {
    "name": "Rock",
    "default_vals": [
        7, 5, 4, 1, -1,
        -1, 1, 4, 5, 7
    ]
}]


class Equalizer:
    def __init__(self, app):
        self.presets = copy.deepcopy(PRESETS)
        for preset in self.presets:
            preset["default"] = True

        self.settings = app.settings
        self.player = app.player

        custom_presets = self.settings.getstring("equalizer", "custom_presets", "").split(",")
        for preset in custom_presets:
            if not preset:
                continue

            data = {
                "name": preset,
                "default": False,
                "default_vals": [0] * 10
            }

            self.presets.append(data)

        for preset in self.presets:
            preset["vals"] = []
            for i in range(0, 10):
                preset["vals"].append(self.settings.getint("equalizer", preset["name"] + "#" + str(i), preset["default_vals"][i]))

        self.active_preset = ""
        self.set_preset(self.settings.getstring("equalizer", "active_preset", "Default"))

    def has_preset(self, name):
        for preset in self.presets:
            if preset["name"] == name:
                return True

        return False

    def __get_preset(self, name):
        preset = None
        for obj in self.presets:
            if obj["name"] == name:
                preset = obj
                break

        return preset

    def set_preset(self, name):
        preset = self.__get_preset(name)

        if not preset or name == self.active_preset:
            return

        self.active_preset = name

        for i in range(0, 10):
            self.player.set_equalizer(i, preset["vals"][i])

        self.settings.setstring("equalizer", "active_preset", name)

    def get_presets(self):
        return [preset["name"] for preset in self.presets]

    def get_active_preset(self):
        return self.__get_preset(self.active_preset)

    def add_preset(self, name):
        if self.has_preset(name):
            return

        self.presets.append({
            "name": name,
            "default": False,
            "vals": [0] * 10,
            "default_vals": [0] * 10
        })
        self.__save_custom_preset_list()

    def __save_custom_preset_list(self):
        custom_presets = [preset["name"] for preset in self.presets if not preset["default"]]
        self.settings.setstring("equalizer", "custom_presets", ",".join(custom_presets))

    def remove_preset(self, name):
        for index, preset in enumerate(self.presets):
            if preset["name"] == name and not preset["default"]:
                del self.presets[index]

                for i in range(0, 10):
                    self.settings.delete("equalizer", name + "#" + str(i))

                if name == self.active_preset:
                    self.set_preset("Default")
                self.__save_custom_preset_list()
                return

    def set_preset_val(self, name, index, val):
        preset = self.__get_preset(name)
        val = int(val)

        preset["vals"][index] = val
        if name == self.active_preset:
            self.player.set_equalizer(index, val)

        if val != preset["default_vals"][index]:
            self.settings.setint("equalizer", preset["name"] + "#" + str(index), val)
        else:
            self.settings.delete("equalizer", preset["name"] + "#" + str(index))

    def reset_preset(self, name):
        preset = self.__get_preset(name)

        for i in range(0, 10):
            preset["vals"][i] = preset["default_vals"][i]
            self.settings.delete("equalizer", preset["name"] + "#" + str(i))

    def rename_preset(self, name, new_name):
        preset = self.__get_preset(name)
        preset["name"] = new_name

        for i in range(0, 10):
            self.settings.delete("equalizer", name + "#" + str(i))
            if preset["vals"][i] != preset["default_vals"][i]:
                self.settings.setint("equalizer", preset["name"] + "#" + str(i), preset["vals"][i])

        if name == self.active_preset:
            self.active_preset = new_name

        self.__save_custom_preset_list()
