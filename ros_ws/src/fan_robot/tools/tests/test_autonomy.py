from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('c++'), 'A host C++ compiler is needed for observation tests.')
class AutonomyTests(unittest.TestCase):
    def test_safe_output_initialization(self):
        self.compile_and_run('safe_outputs_test')

    def test_closed_loop_and_supervisor(self):
        self.compile_and_run('autonomy_test')

    def compile_and_run(self, name):
        firmware = Path(__file__).resolve().parents[2] / 'firmware'
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / name
            subprocess.run([
                shutil.which('c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                '-I', str(firmware / 'esp32_hand' / 'main'),
                str(firmware / 'tests' / (name + '.cpp')),
                '-o', str(executable),
            ], check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)


@unittest.skipUnless(shutil.which('node'), 'Node.js is needed for autonomy page tests.')
class AutonomyPageTests(unittest.TestCase):
    def test_session_and_disconnect(self):
        firmware = Path(__file__).resolve().parents[2] / 'firmware'
        subprocess.run([shutil.which('node'), str(firmware / 'tests' / 'autonomy_page_test.js')],
                       check=True, capture_output=True, text=True)


if __name__ == '__main__':
    unittest.main()
