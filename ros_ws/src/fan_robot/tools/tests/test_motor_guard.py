from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('c++'), 'A host C++ compiler is needed for motor guard tests.')
class MotorGuardTests(unittest.TestCase):
    def test_motor_safety_state_machine(self):
        firmware = Path(__file__).resolve().parents[2] / 'firmware'
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'motor_guard_test'
            subprocess.run([
                shutil.which('c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                '-I', str(firmware / 'esp32_motor_manual'),
                str(firmware / 'tests' / 'motor_guard_test.cpp'),
                '-o', str(executable),
            ], check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
