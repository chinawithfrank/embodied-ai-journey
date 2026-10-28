import argparse
from datetime import datetime, timezone
from http.client import HTTPException
import json
import math
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener


MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def camera_origin(value):
    parsed = urlsplit(value)
    try:
        parsed.port
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    if (
        parsed.scheme not in ('http', 'https')
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ('', '/')
        or parsed.query
        or parsed.fragment
    ):
        raise argparse.ArgumentTypeError(
            'Use a camera origin such as http://192.168.4.1 (without a path).')
    return value.rstrip('/')


def positive_number(value):
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('Enter a positive number.') from error
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('Enter a finite number greater than zero.')
    return number


def fetch(origin, endpoint, timeout):
    request = Request(origin + endpoint, headers={'Cache-Control': 'no-cache'})
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            content_type = response.headers.get_content_type()
    except HTTPError as error:
        detail = error.read(256).decode('utf-8', errors='replace')
        raise RuntimeError(f'Camera returned HTTP {error.code}: {detail}') from error
    except (URLError, TimeoutError, OSError, HTTPException) as error:
        raise RuntimeError(
            f'Cannot read {origin + endpoint}: {error}. '
            'Check camera power, Wi-Fi, the IP address, and /health.') from error
    if len(payload) > MAX_RESPONSE_BYTES:
        raise RuntimeError('Camera response exceeded the 4 MiB size limit.')
    return content_type, payload


def read_health(origin, timeout):
    content_type, payload = fetch(origin, '/health', timeout)
    if content_type != 'application/json':
        raise RuntimeError(f'Expected camera JSON, received {content_type}.')
    try:
        health = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as error:
        raise RuntimeError('Camera returned invalid JSON.') from error
    if not isinstance(health, dict) or not isinstance(health.get('camera_ready'), bool):
        raise RuntimeError('Response is not a fan-robot camera health report.')
    return health


def read_jpeg(origin, timeout):
    content_type, payload = fetch(origin, '/capture', timeout)
    if content_type != 'image/jpeg':
        raise RuntimeError(f'Expected image/jpeg, received {content_type}.')
    if not payload.startswith(b'\xff\xd8') or b'\xff\xd9' not in payload[-4096:]:
        raise RuntimeError('Response is missing JPEG markers; the frame may be truncated.')
    return payload


def save_snapshot(origin, timeout, output):
    payload = read_jpeg(origin, timeout)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as image_file:
        image_file.write(payload)
    print(f'Saved {len(payload)} bytes to {output.resolve()}')


def view_camera(origin, timeout, fps, output_directory):
    try:
        import cv2
        import numpy as np
    except ImportError as error:
        raise RuntimeError(
            'Preview needs GUI OpenCV: install tools/requirements.txt in an isolated venv. '
            'The check and snapshot commands need only Python.') from error

    print('q: quit | s: save current frame. Close other camera viewers first.')
    try:
        while True:
            started = time.monotonic()
            payload = read_jpeg(origin, timeout)
            frame = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                raise RuntimeError('OpenCV could not decode the camera JPEG.')
            cv2.imshow('Fan robot camera', frame)
            wait_ms = max(1, int((1.0 / fps - (time.monotonic() - started)) * 1000))
            key = cv2.waitKey(wait_ms) & 0xFF
            if key == ord('q'):
                break
            if key == ord('s'):
                filename = datetime.now(timezone.utc).strftime('frame_%Y%m%dT%H%M%S_%fZ.jpg')
                output_directory.mkdir(parents=True, exist_ok=True)
                output = output_directory / filename
                with output.open('xb') as image_file:
                    image_file.write(payload)
                print(f'Saved {output.resolve()}')
    except cv2.error as error:
        raise RuntimeError(
            f'OpenCV preview failed: {error}. Use a desktop session and GUI OpenCV, '
            'or use the browser/snapshot command without a GUI.') from error
    finally:
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inspect and capture the ESP32 fan-robot camera.')
    parser.add_argument('--url', type=camera_origin, default='http://192.168.4.1')
    parser.add_argument('--timeout', type=positive_number, default=5.0)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('check', help='Read camera status; exit 1 if the camera is not ready.')
    snapshot = commands.add_parser('snapshot', help='Save a JPEG without third-party dependencies.')
    snapshot.add_argument('--output', type=Path, default=Path('captures/frame.jpg'))
    view = commands.add_parser('view', help='Preview snapshots using optional GUI OpenCV.')
    view.add_argument('--fps', type=positive_number, default=5.0)
    view.add_argument('--output-dir', type=Path, default=Path('captures'))
    arguments = parser.parse_args(argv)
    try:
        health = read_health(arguments.url, arguments.timeout)
        if arguments.command == 'check':
            print(json.dumps(health, indent=2, ensure_ascii=False))
            return 0 if health['camera_ready'] else 1
        if not health['camera_ready']:
            raise RuntimeError(f'Camera is not ready: {health.get("status", "unknown")}.')
        if arguments.command == 'snapshot':
            save_snapshot(arguments.url, arguments.timeout, arguments.output)
        else:
            view_camera(
                arguments.url, arguments.timeout, arguments.fps, arguments.output_dir)
    except KeyboardInterrupt:
        return 130
    except (RuntimeError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
