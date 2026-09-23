import argparse
import os
from pathlib import Path

DEFAULT_DATASET_URL = (
    'https://universe.roboflow.com/yolov8-training-o2cxu/'
    'tennis_yolo/dataset/1'
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Download the public Tennis_Yolo dataset in YOLO format.')
    parser.add_argument(
        '--dataset-url', default=DEFAULT_DATASET_URL,
        help='Public Roboflow Universe dataset URL.')
    parser.add_argument(
        '--output', type=Path, default=Path('data'),
        help='Directory where the downloaded dataset and manifest are stored.')
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    output_directory = arguments.output.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    try:
        import roboflow
        from roboflow.config import load_roboflow_api_key
    except ImportError as error:
        raise SystemExit(
            'Missing dependency: run pip install -r requirements.txt first.') from error

    if not load_roboflow_api_key():
        raise SystemExit(
            'Roboflow API key is required to download this public dataset. '
            'Get a private key from your Roboflow workspace settings, set '
            'ROBOFLOW_API_KEY in this terminal, and retry.')

    original_directory = Path.cwd()
    try:
        os.chdir(output_directory)
        dataset = roboflow.download_dataset(
            dataset_url=arguments.dataset_url,
            model_format='yolov8',
        )
    finally:
        os.chdir(original_directory)

    dataset_directory = Path(dataset.location).resolve()
    data_file = dataset_directory / 'data.yaml'
    if not data_file.is_file():
        raise SystemExit(f'Roboflow download has no data.yaml: {dataset_directory}')

    manifest_path = output_directory / 'last_download.txt'
    manifest_path.write_text(f'{data_file}\n', encoding='utf-8')
    print(f'Dataset downloaded to: {dataset_directory}')
    print(f'Dataset manifest: {manifest_path}')
    print(
        'Next step: python3 -m yolo_tennis_ball.train '
        f'--data {manifest_path}')


if __name__ == '__main__':
    main()
