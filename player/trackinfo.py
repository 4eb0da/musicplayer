import re


class TrackInfo:
    @staticmethod
    def check_tags(tags):
        return (
            tags and
            tags.get("TITLE", None) and tags["TITLE"][0] and
            tags.get("ALBUM", None) and tags["ALBUM"][0] and
            tags.get("ARTIST", None) and tags["ARTIST"][0]
        )

    # russian letters encoding fix
    LETTERS = "абвгдеёжзийклмнопрстуфхцчшщьыъэюя"
    LETTERS += LETTERS.upper()
    LETTERS = LETTERS.encode("cp1251").decode("cp1252")

    @staticmethod
    def convert(string):
        if re.search("[" + TrackInfo.LETTERS + "]", string):
            return string.encode("cp1252").decode("cp1251")
        return string

    def __init__(self, tags):
        self.title = self.convert(tags["TITLE"][0])
        self.album = self.convert(tags["ALBUM"][0])
        self.artist = self.convert(tags["ARTIST"][0])

    def __str__(self):
        return self.title + " - " + self.album + " - " + self.artist
