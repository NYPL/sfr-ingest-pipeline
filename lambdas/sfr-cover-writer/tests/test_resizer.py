from PIL import Image
import pytest

from lib.resizer import CoverResizer


class TestCoverResize:
    @pytest.fixture
    def mockLoad(self, mocker):
        return mocker.patch.object(CoverResizer, 'loadOriginal')

    @pytest.fixture
    def mockData(self, mocker):
        return mocker.patch.object(CoverResizer, 'loadImageData')

    def test_init_resizer(self, mockLoad, mockData):
        testResizer = CoverResizer('testImageBytes')
        assert isinstance(testResizer, CoverResizer)
        mockLoad.assert_called_once_with('testImageBytes')
        mockData.assert_called_once()

    def test_loadOriginal(self, mocker, mockData):
        mockImage = mocker.patch.object(Image, 'open')
        mockBytes = mocker.patch('lib.resizer.BytesIO', return_value='testB')
        mockImage.return_value = 'pillow_image'
        testResizer = CoverResizer('testImageBytes')
        assert testResizer.original == 'pillow_image'
        mockBytes.assert_called_once_with('testImageBytes')
        mockImage.assert_called_once_with('testB')
        mockData.assert_called_once()

    def test_loadImageData(self, mocker, mockLoad):
        mockImg = mocker.MagicMock()
        mockImg.width = 300
        mockImg.height = 400
        mockImg.format = 'test'
        mockLoad.return_value = mockImg
        testResizer = CoverResizer('testImageBytes')
        assert testResizer.oWidth == 300
        assert testResizer.oHeight == 400
        assert testResizer.format == 'test'

    def test_getNewDimensions_long(self, mockLoad, mockData):
        testResizer = CoverResizer('testImageBytes')
        testResizer.oWidth = 450
        testResizer.oHeight = 900

        testResizer.getNewDimensions()

        assert testResizer.rHeight == 400
        assert testResizer.rWidth == 200

    def test_getNewDimensions_short(self, mockLoad, mockData):
        testResizer = CoverResizer('testImageBytes')
        testResizer.oWidth = 500
        testResizer.oHeight = 350

        testResizer.getNewDimensions()

        assert testResizer.rHeight == 210
        assert testResizer.rWidth == 300

    def test_getNewDimensions_square(self, mockLoad, mockData):
        testResizer = CoverResizer('testImageBytes')
        testResizer.oWidth = 550
        testResizer.oHeight = 600

        testResizer.getNewDimensions()

        assert testResizer.rHeight == 275
        assert testResizer.rWidth == 300

    def test_resizeCover(self, mocker, mockLoad, mockData):
        testImg = mocker.MagicMock()
        testImg.resize.return_value = 'resizedImage'
        mockLoad.return_value = testImg
        testResizer = CoverResizer('testImageBytes')
        testResizer.rWidth = 300
        testResizer.rHeight = 400
        testResizer.resizeCover()
        assert testResizer.standard == 'resizedImage'
        testImg.resize.assert_called_once_with((300, 400))

    def test_getCoverInBytes(self, mocker, mockLoad, mockData):
        mockIO = mocker.patch('lib.resizer.BytesIO')
        mockBytes = mocker.MagicMock()
        mockIO.return_value = mockBytes
        mockBytes.getvalue.return_value = 'standardBytes'
        testResizer = CoverResizer('testImageBytes')

        testResizer.standard = mocker.MagicMock()
        testResizer.format = 'test'

        testOut = testResizer.getCoverInBytes()

        assert testOut == 'standardBytes'
        testResizer.standard.save.assert_called_once_with(
            mockBytes, format='test'
        )
