import argparse
from pathlib import Path


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Fine-tune a YOLO detector for a single tennis-ball class.')
    parser.add_argument(
        '--data', type=Path, default=Path('data/last_download.txt'),
        help='YOLO data.yaml or the manifest written by download_dataset.py.')
    parser.add_argument('--model', default='yolo26n.pt')
    parser.add_argument('--epochs', type=int, default=80)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--batch', type=int, default=-1)
    parser.add_argument('--device', default='0')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--project', type=Path, default=Path('runs'))
    parser.add_argument('--name', default='tennis_ball_yolo26')
    return parser.parse_args()


def resolve_data_file(path):
    requested_path = path.resolve()
    if requested_path.suffix == '.txt':
        requested_path = Path(
            requested_path.read_text(encoding='utf-8').strip()).resolve()
    if not requested_path.is_file():
        raise SystemExit(f'YOLO dataset file does not exist: {requested_path}')
    return requested_path


def main():
    arguments = parse_arguments()
    data_file = resolve_data_file(arguments.data)
    project_directory = arguments.project.resolve()

    try:
        from ultralytics import YOLO
    except ImportError as error:
        raise SystemExit(
            'Missing dependency: run pip install -r requirements.txt first.') from error

    model = YOLO(arguments.model)
    model.train(
        data=str(data_file),
        epochs=arguments.epochs,
        imgsz=arguments.imgsz,
        batch=arguments.batch,
        device=arguments.device,
        workers=arguments.workers,
        project=str(project_directory),
        name=arguments.name,
        exist_ok=True,
    )
    print(
        'Training complete. Camera command: python3 -m '
        'yolo_tennis_ball.webcam_detector --model '
        f'{project_directory / arguments.name / "weights" / "best.pt"}')


if __name__ == '__main__':
    main()
