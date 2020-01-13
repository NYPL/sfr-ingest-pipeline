from PIL import Image
from io import BytesIO


class CoverResizer:
    def __init__(self, coverBytes):
        self.original = self.loadOriginal(coverBytes)
        self.loadImageData()

    def loadOriginal(self, coverBytes):
        return Image.open(BytesIO(coverBytes))

    def loadImageData(self):
        self.oWidth = self.original.width
        self.oHeight = self.original.height
        self.format = self.original.format

    def getNewDimensions(self):
        originalRatio = self.oWidth / self.oHeight

        if 400 * originalRatio > 300:
            if originalRatio > 1:
                self.rHeight = int(round(300 / originalRatio))
            else:
                self.rHeight = int(round(300 * originalRatio))
            self.rWidth = 300
        else:
            self.rHeight = 400
            self.rWidth = int(round(400 * originalRatio))

    def resizeCover(self):
        self.standard = self.original.resize((self.rWidth, self.rHeight))

    def getCoverInBytes(self):
        outBytes = BytesIO()
        self.standard.save(outBytes, format=self.format)
        return outBytes.getvalue()

