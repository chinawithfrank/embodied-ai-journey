from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('c++'), 'A host C++ compiler is needed for fan guard tests.')
class FanGuardTests(unittest.TestCase):
    def test_fan_safety_and_motor_independence(self):
        firmware = Path(__file__).resolve().parents[2] / 'firmware'
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'fan_guard_test'
            subprocess.run([
                shutil.which('c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                '-I', str(firmware / 'esp32_fan_manual'),
                '-I', str(firmware / 'esp32_motor_manual'),
                str(firmware / 'tests' / 'fan_guard_test.cpp'), '-o', str(executable),
            ], check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


@unittest.skipUnless(shutil.which('node'), 'Node.js is needed for fan page tests.')
class FanPageTests(unittest.TestCase):
    def test_fan_page_lease_and_stop(self):
        firmware = Path(__file__).resolve().parents[2] / 'firmware'
        subprocess.run([
            shutil.which('node'), str(firmware / 'tests' / 'fan_page_test.js'),
        ], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
