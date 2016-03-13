import re
import os


class TrackInfo:
    # russian letters encoding fix
    LETTERS = "абвгдеёжзийклмнопрстуфхцчшщьыъэюя"
    LETTERS += LETTERS.upper()
    LETTERS = LETTERS.encode("cp1251").decode("cp1252")

    @staticmethod
    def convert(string):
        if re.search("[" + TrackInfo.LETTERS + "]", string):
            return string.encode("cp1252").decode("cp1251")
        return string

    def __init__(self, fullpath, tags):
        self.title = self.convert("TITLE" in tags and tags["TITLE"][0] or os.path.basename(fullpath))
        self.album = self.convert("ALBUN" in tags and tags["ALBUM"][0] or "Unknown")
        self.artist = self.convert("ARTIST" in tags and tags["ARTIST"][0] or "Unknown")

    def __str__(self):
        return self.title + " - " + self.album + " - " + self.artist
