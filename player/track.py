import os

class Track:
    def __init__(self, filename):
        self.filename = os.path.basename(filename)
        self.fullpath = filename
        self.info = None

    def name(self):
        if self.info and self.info["TITLE"]:
            return self.info["TITLE"][0]

        return self.filename

    def __str__(self):
        return self.filename
