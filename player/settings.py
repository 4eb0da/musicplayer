import os
from configparser import ConfigParser


class Settings:
    def __init__(self, app):
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

    def save(self):
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
