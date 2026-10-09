import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.isbn import extract_image_url
from src.thumbnail import NDL_HEADERS, download_image, fetch_ndl, process_thumbnail


def image_bytes():
    buffer = BytesIO()
    Image.new("RGB", (10, 10), "navy").save(buffer, "JPEG")
    return buffer.getvalue()


class ThumbnailTests(unittest.TestCase):
    def test_opac_placeholder_is_not_treated_as_a_cover(self):
        html = '''
            <meta property="og:image" content="/images/bookimage-kango.png">
            <img id="lid_intro_thumbnail" src="/images/bookimage-kango.png">
        '''

        self.assertEqual(extract_image_url(html), "")

    def test_ndl_request_includes_its_required_referer(self):
        with patch("src.thumbnail.fetch_content", return_value=b"x" * 1001) as fetch:
            self.assertIsNotNone(fetch_ndl("9784003101018"))

        fetch.assert_called_once_with(
            "https://ndlsearch.ndl.go.jp/thumbnail/9784003101018.jpg",
            headers=NDL_HEADERS,
        )

    def test_invalid_opac_image_falls_back_to_ndl(self):
        cover = image_bytes()
        with (
            patch("src.thumbnail.fetch_content", return_value=b"not an image"),
            patch("src.thumbnail.fetch_google", return_value=None),
            patch("src.thumbnail.fetch_ndl", return_value=cover) as ndl,
            patch("src.thumbnail.fetch_openlibrary", return_value=None),
        ):
            self.assertEqual(
                download_image(
                    "9784003101018",
                    "テスト書籍",
                    "/cover.jpg",
                    "https://opac.example.test/book/1",
                ),
                cover,
            )

        ndl.assert_called_once_with("9784003101018")

    def test_relative_opac_image_is_resolved_and_saved(self):
        cover = image_bytes()
        with tempfile.TemporaryDirectory() as directory, patch(
            "src.thumbnail.get_image_dir", return_value=directory
        ), patch("src.thumbnail.fetch_content", return_value=cover) as fetch:
            path = process_thumbnail(
                "9784003101018",
                "テスト書籍",
                "/images/cover.jpg",
                "https://opac.example.test/book/1",
            )
            self.assertTrue(Path(path).is_file())

        self.assertTrue(path.endswith("9784003101018-v2.jpeg"))
        fetch.assert_called_once_with(
            "https://opac.example.test/images/cover.jpg",
            headers={"Referer": "https://opac.example.test/book/1"},
        )


if __name__ == "__main__":
    unittest.main()
