import argparse
from pathlib import Path


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Capture hand-held tennis-ball images for later annotation.')
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--output', type=Path, default=Path('captures/handheld'))
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    try:
        import cv2
    except ImportError as error:
        raise SystemExit(
            'Missing dependency: run pip install -r requirements.txt first.') from error

    output_directory = arguments.output.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    camera = cv2.VideoCapture(arguments.camera)
    if not camera.isOpened():
        raise SystemExit(f'Cannot open camera index {arguments.camera}.')

    image_index = len(list(output_directory.glob('*.jpg')))
    print('Press Space to save an image. Press q to quit.')
    try:
        while True:
            success, frame = camera.read()
            if not success:
                raise RuntimeError('Camera frame capture failed.')
            cv2.putText(
                frame, 'Space: save hand-held sample | q: quit', (16, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2,
                cv2.LINE_AA)
            cv2.imshow('Capture tennis-ball samples', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            if key == ord(' '):
                image_path = output_directory / f'handheld_{image_index:04d}.jpg'
                cv2.imwrite(str(image_path), frame)
                print(f'Saved {image_path}')
                image_index += 1
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
