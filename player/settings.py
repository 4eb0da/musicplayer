import os
from gi.repository import GObject
from configparser import ConfigParser


class Settings:
    def __init__(self, app):
        self.save_delay = None
        self.config = ConfigParser()
        self.config_dir = os.environ["HOME"] + "/.config/" + app.APP_CONFIG_PATH
        self.config_path = self.config_dir + "/config.ini"
        self.config.read(self.config_path)

    def getboolean(self, section, name, fallback):
        return self.config.getboolean(section, name, fallback=fallback)

    def setboolean(self, section, name, value):
        if section not in self.config.sections():
            self.config.add_section(section)
        self.config.set(section, name, "yes" if value else "no")
        self.__save()

    def getstring(self, section, name, fallback):
        return self.config.get(section, name, fallback=fallback)

    def setstring(self, section, name, value):
        if section not in self.config.sections():
            self.config.add_section(section)
        self.config.set(section, name, value)
        self.__save()

    def getint(self, section, name, fallback):
        return self.config.getint(section, name, fallback=fallback)

    def setint(self, section, name, value):
        if section not in self.config.sections():
            self.config.add_section(section)
        self.config.set(section, name, str(int(value)))
        self.__save()

    def delete(self, section, name):
        if section in self.config and name in self.config[section]:
            del self.config[section][name]
            self.__save()

    def __save(self):
        def save() :
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)

        if self.save_delay is not None:
            GObject.source_remove(self.save_delay)
        self.save_delay = GObject.timeout_add(50, save)
