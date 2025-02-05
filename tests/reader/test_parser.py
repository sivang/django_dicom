# import array
import datetime
import pydicom

from django.test import TestCase
from django_dicom.reader import DicomParser
from tests.fixtures import TEST_DWI_IMAGE_PATH


class DicomParserTestCase(TestCase):
    def setUp(self):
        self.header = pydicom.dcmread(TEST_DWI_IMAGE_PATH, stop_before_pixels=True)
        self.parser = DicomParser()

    def test_parse_age_string(self):
        data_element = self.header.data_element("PatientAge")
        result = self.parser.parse_age_string(data_element)
        expected = 27.0
        self.assertEqual(result, expected)

    def test_parse_decimal_string(self):
        names = {"MagneticFieldStrength", "EchoTime", "RepetitionTime"}
        for name in names:
            data_element = self.header.data_element(name)
            result = self.parser.parse_decimal_string(data_element)
            expected = float(data_element.value)
            self.assertEqual(result, expected)

    def test_parse_decimal_string_with_value_multiplicity(self):
        data_element = self.header.data_element("PixelSpacing")
        result = self.parser.parse_decimal_string(data_element)
        expected = [float(value) for value in data_element.value]
        self.assertListEqual(result, expected)

    def test_parse_integer_string(self):
        names = {"InstanceNumber", "SeriesNumber", "NumberOfAverages"}
        for name in names:
            data_element = self.header.data_element(name)
            result = self.parser.parse_integer_string(data_element)
            expected = int(data_element.value)
            self.assertEqual(result, expected)

    def test_parse_date(self):
        names = {"InstanceCreationDate", "StudyDate", "SeriesDate"}
        for name in names:
            data_element = self.header.data_element(name)
            result = self.parser.parse_date(data_element)
            expected = datetime.datetime.strptime(data_element.value, "%Y%m%d").date()
            self.assertEqual(result, expected)

    def test_parse_time(self):
        names = {"InstanceCreationTime", "StudyTime", "SeriesTime"}
        for name in names:
            data_element = self.header.data_element(name)
            result = self.parser.parse_time(data_element)
            expected = datetime.datetime.strptime(
                data_element.value, "%H%M%S.%f"
            ).time()
            self.assertEqual(result, expected)

    def test_parse_datetime(self):
        # It turns out the current test DICOM file doesn't actually have any
        # Date Time (DT) data elements, so once we have one that does we should
        # complete this test.

        # names = {}
        # for name in names:
        #     data_element = self.header.data_element(name)
        #     result = self.parser.parse_datetime(data_element)
        #     expected = datetime.strptime(element.value, "%Y%m%d%H%M%S.%f")
        #     self.assertEqual(result, expected)
        pass

    def test_parse_code_string(self):
        names = {"ScanningSequence": ["EP"], "SequenceVariant": ["SK", "SP"]}
        for name in names.keys():
            data_element = self.header.data_element(name)
            result = self.parser.parse_code_string(data_element)
            expected = names.get(name)
            self.assertEqual(result, expected)

    def test_parse_code_string_with_single_value(self):
        names = {"PatientSex": "M", "PatientPosition": "HFS", "Modality": "MR"}
        for name in names.keys():
            data_element = self.header.data_element(name)
            result = self.parser.parse_code_string(data_element)
            expected = names.get(name)
            self.assertEqual(result, expected)

    def test_parse_code_string_without_enum(self):
        names = {"BodyPartExamined", "ScanOptions"}
        for name in names:
            data_element = self.header.data_element(name)
            result = self.parser.parse_code_string(data_element)
            expected = data_element.value
            self.assertEqual(result, expected)

    # SIEMENS tags
    def test_parse_siemens_num_images_in_mosaic(self):
        tag = ("0019", "100A")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        expected = 60
        # expected = int.from_bytes(data_element.value, byteorder="little")
        self.assertEqual(result, expected)

    def test_parse_siemens_slice_measurement_duration(self):
        tag = ("0019", "100B")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        expected = 305000.0
        # expected = float(data_element.value)
        self.assertEqual(result, expected)

    def test_parse_siemens_b_value(self):
        tag = ("0019", "100C")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        expected = 0
        # expected = int(data_element.value)
        self.assertEqual(result, expected)

    def test_parse_siemens_diffusion_directionality(self):
        tag = ("0019", "100D")
        data_element = self.header.get(tag)
        if isinstance(data_element, pydicom.DataElement):
            result = self.parser.parse(data_element)
            expected = "DIRECTIONAL"
            # expected = data_element.value.decode("utf-8").strip()
            self.assertEqual(result, expected)
        else:
            self.fail(
                f"Failed to read diffusion directionality [{tag}] from test file!"
            )

    def test_parse_siemens_gradient_direction(self):
        tag = ("0019", "100E")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        expected = [0.70710677, -0.70710677, 0.0]
        # expected = [
        #     float(value) for value in list(array.array("d", data_element.value))
        # ]
        self.assertListEqual(result, expected)

    def test_parse_siemens_gradient_mode(self):
        tag = ("0019", "100F")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        # expected = data_element.value.decode("utf-8").strip()
        expected = ""
        self.assertEqual(result, expected)

    def test_parse_siemens_b_matrix(self):
        tag = ("0019", "1027")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        expected = [1.0, -1.0, 0.0, 1.0, 0.0, 0.0]
        # expected = list(array.array("d", data_element.value))
        self.assertListEqual(result, expected)

    def test_parse_siemens_bandwidth_per_pixel_phase_encode(self):
        tag = ("0019", "1028")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        expected = 40.584
        # expected = array.array("d", data_element.value)[0]
        self.assertEqual(result, expected)

    def test_parse_siemens_slice_timing(self):
        tag = ("0019", "1029")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        expected = TEST_DWI_B_MATRIX
        # expected = [
        #     round(slice_time, 5)
        #     for slice_time in list(array.array("d", data_element.value))
        # ]
        self.assertListEqual(result, expected)

    def test_parsing_unknown_element(self):
        tag = ("0051", "1015")
        data_element = self.header.get(tag)
        result = self.parser.parse(data_element)
        expected = data_element.value
        self.assertEqual(result, expected)

    def test_parse_with_keywords(self):
        expected = {
            "PatientAge": 27.0,
            "StudyDate": datetime.date(2018, 5, 1),
            "StudyTime": datetime.time(12, 21, 56, 958000),
        }
        for key, value in expected.items():
            data_element = self.header.data_element(key)
            result = self.parser.parse(data_element)
            self.assertEqual(result, value)

    def test_parse_with_tags(self):
        expected = {
            # Series Number attribute with Integer String (IS) value-representation
            ("0020", "0011"): 13,
            # Echo Time attribute with Decimal String (DS) value-representation
            ("0018", "0081"): 94.0,
            # Modality attribute with Code String (CS) value-representation
            ("0008", "0060"): "MR",
            # Diffusion Directionality attribute with Unknown (UN) value-representation
            ("0019", "100d"): "DIRECTIONAL",
        }
        for key, value in expected.items():
            data_element = self.header.get(key)
            result = self.parser.parse(data_element)
            self.assertEqual(result, value)

    def test_parse_with_invalid_value_representation(self):
        data_element = self.header.data_element("StudyInstanceUID")
        data_element.VR = "KITTENS"
        with self.assertRaises(NotImplementedError):
            self.parser.parse(data_element)

    def test_parse_with_value_representation_that_has_no_parsing_method(self):
        # We'll use a Unique Identifier (UI) data element, because we don't need
        # to parse it (we use its string representation as it is returned from
        # the raw headers).
        data_element = self.header.data_element("StudyInstanceUID")

        # Let's make sure we really did not assign any parsing method to it.
        self.assertIsNone(self.parser.PARSING_METHOD.get(data_element.VR))

        # Because no parsing method is assigned, the parser should simply
        # return the raw value.
        parsed = self.parser.parse(data_element)
        self.assertEqual(data_element.value, parsed)


TEST_DWI_B_MATRIX = [
    2460.0,
    0.0,
    1640.0,
    165.0,
    1805.0,
    327.5,
    1967.5,
    492.5,
    2132.5,
    655.0,
    2295.0,
    985.0,
    2625.0,
    1147.5,
    2787.5,
    1312.5,
    2952.5,
    1475.0,
    3115.0,
    820.0,
    2460.0,
    0.0,
    1640.0,
    165.0,
    1805.0,
    327.5,
    1967.5,
    492.5,
    2132.5,
    655.0,
    2295.0,
    985.0,
    2625.0,
    1147.5,
    2787.5,
    1312.5,
    2952.5,
    1475.0,
    3115.0,
    820.0,
    2460.0,
    0.0,
    1640.0,
    165.0,
    1805.0,
    327.5,
    1967.5,
    492.5,
    2132.5,
    655.0,
    2295.0,
    985.0,
    2625.0,
    1147.5,
    2787.5,
    1312.5,
    2952.5,
    1475.0,
    3115.0,
    820.0,
]
