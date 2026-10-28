from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('c++'), 'A host C++ compiler is needed for observation tests.')
class HandObservationTests(unittest.TestCase):
    def test_target_selection_and_expiry(self):
        firmware = Path(__file__).resolve().parents[2] / 'firmware'
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'hand_observation_test'
            subprocess.run([
                shutil.which('c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                '-I', str(firmware / 'esp32_hand' / 'main'),
                str(firmware / 'tests' / 'hand_observation_test.cpp'),
                '-o', str(executable),
            ], check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
