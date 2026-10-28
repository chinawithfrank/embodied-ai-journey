from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('c++'), 'A host C++ compiler is needed for the clock guard test.')
class CameraClockTests(unittest.TestCase):
    def test_clock_guards(self):
        firmware_directory = Path(__file__).resolve().parents[2] / 'firmware'
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'camera_clock_test'
            subprocess.run([
                shutil.which('c++'), '-std=c++11', '-Wall', '-Wextra', '-Werror',
                '-I', str(firmware_directory / 'esp32_camera'),
                str(firmware_directory / 'tests' / 'camera_clock_test.cpp'),
                '-o', str(executable),
            ], check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
