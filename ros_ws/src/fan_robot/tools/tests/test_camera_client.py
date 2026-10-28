import contextlib
import importlib.util
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest


client_path = Path(__file__).resolve().parents[1] / 'camera_client.py'
module_spec = importlib.util.spec_from_file_location('camera_client', client_path)
camera_client = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(camera_client)


class CameraHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            content_type = 'application/json'
            payload = json.dumps(self.server.health).encode()
            status = 200
        elif self.path == '/capture':
            content_type = self.server.image_type
            payload = self.server.image
            status = self.server.image_status
        else:
            content_type = 'text/plain'
            payload = b'not found'
            status = 404
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format_string, *arguments):
        pass


class CameraClientTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), CameraHandler)
        self.server.health = {'camera_ready': True, 'status': 'ready', 'sensor': 'OV2640'}
        self.server.image_type = 'image/jpeg'
        self.server.image_status = 200
        self.server.image = b'\xff\xd8transport-test\xff\xd9'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def run_client(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return camera_client.main(['--url', self.origin, *arguments])

    def test_check_ready(self):
        self.assertEqual(self.run_client('check'), 0)

    def test_check_reports_unconfigured_camera(self):
        self.server.health = {'camera_ready': False, 'status': 'wiring_not_confirmed'}
        self.assertEqual(self.run_client('check'), 1)

    def test_reject_unrelated_health_endpoint(self):
        self.server.health = {'status': 'ok'}
        with self.assertRaisesRegex(RuntimeError, 'health report'):
            camera_client.read_health(self.origin, 1)

    def test_snapshot_saves_camera_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'captures' / 'frame.jpg'
            self.assertEqual(self.run_client('snapshot', '--output', str(output)), 0)
            self.assertEqual(output.read_bytes(), self.server.image)

    def test_snapshot_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'frame.jpg'
            output.write_bytes(b'keep this file')
            self.assertEqual(self.run_client('snapshot', '--output', str(output)), 1)
            self.assertEqual(output.read_bytes(), b'keep this file')

    def test_snapshot_requires_ready_camera(self):
        self.server.health['camera_ready'] = False
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'frame.jpg'
            self.assertEqual(self.run_client('snapshot', '--output', str(output)), 1)
            self.assertFalse(output.exists())

    def test_http_error_includes_diagnostic(self):
        self.server.image_status = 503
        self.server.image_type = 'text/plain'
        self.server.image = b'jpeg_capture_failed'
        with self.assertRaisesRegex(RuntimeError, 'HTTP 503: jpeg_capture_failed'):
            camera_client.read_jpeg(self.origin, 1)

    def test_reject_non_jpeg(self):
        self.server.image_type = 'text/html'
        with self.assertRaisesRegex(RuntimeError, 'Expected image/jpeg'):
            camera_client.read_jpeg(self.origin, 1)

    def test_reject_truncated_frame(self):
        self.server.image = b'\xff\xd8incomplete'
        with self.assertRaisesRegex(RuntimeError, 'truncated'):
            camera_client.read_jpeg(self.origin, 1)

    def test_allow_sensor_padding_after_end_marker(self):
        self.server.image += b'\x00' * 16
        self.assertEqual(camera_client.read_jpeg(self.origin, 1), self.server.image)

    def test_response_size_is_bounded(self):
        from unittest.mock import patch

        with patch.object(camera_client, 'MAX_RESPONSE_BYTES', 4):
            with self.assertRaisesRegex(RuntimeError, 'size limit'):
                camera_client.read_jpeg(self.origin, 1)

    def test_interrupted_response_has_a_readable_error(self):
        from http.client import IncompleteRead
        from unittest.mock import patch

        with patch.object(camera_client, 'build_opener') as opener:
            opener.return_value.open.side_effect = IncompleteRead(b'partial', 100)
            with self.assertRaisesRegex(RuntimeError, 'Cannot read'):
                camera_client.read_jpeg(self.origin, 1)

    def test_origins_and_numbers_are_validated(self):
        import argparse

        self.assertEqual(camera_client.camera_origin(self.origin + '/'), self.origin)
        for value in ('file:///tmp/frame.jpg', 'http://camera/stream', 'http://user:pw@camera',
                      'http://camera:bad', 'http://camera?query=1'):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                camera_client.camera_origin(value)
        for value in ('0', '-1', 'nan', 'inf', 'not-a-number'):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                camera_client.positive_number(value)


if __name__ == '__main__':
    unittest.main()
