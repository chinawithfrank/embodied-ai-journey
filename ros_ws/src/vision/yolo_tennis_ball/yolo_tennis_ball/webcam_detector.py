import argparse
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter


@dataclass
class Detection:
    center_x: int
    center_y: int
    confidence: float
    left: int
    top: int
    right: int
    bottom: int


class RosPixelPublisher:
    def __init__(self, topic):
        try:
            import rclpy
            from geometry_msgs.msg import PointStamped
        except ImportError as error:
            raise RuntimeError(
                'ROS publishing requires a sourced ROS2 environment.') from error

        rclpy.init()
        self.rclpy = rclpy
        self.point_type = PointStamped
        self.node = rclpy.create_node('tennis_ball_pixel_detector')
        self.publisher = self.node.create_publisher(PointStamped, topic, 10)

    def publish(self, detection):
        message = self.point_type()
        message.header.stamp = self.node.get_clock().now().to_msg()
        message.header.frame_id = 'camera_pixels'
        message.point.x = float(detection.center_x)
        message.point.y = float(detection.center_y)
        message.point.z = detection.confidence
        self.publisher.publish(message)

    def close(self):
        self.node.destroy_node()
        self.rclpy.shutdown()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Detect a tennis ball and display its image pixel coordinates.')
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--class-name', default='tennis-ball')
    parser.add_argument('--confidence', type=float, default=0.35)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--ros-topic', default=None)
    return parser.parse_args()


def normalized_name(name):
    return name.strip().lower().replace('_', '-').replace(' ', '-')


def choose_detection(result, expected_class):
    selected_detection = None
    expected_name = normalized_name(expected_class)
    for box in result.boxes:
        class_index = int(box.cls.item())
        detected_name = normalized_name(result.names[class_index])
        if detected_name != expected_name:
            continue
        confidence = float(box.conf.item())
        left, top, right, bottom = [
            int(value) for value in box.xyxy[0].tolist()]
        candidate = Detection(
            center_x=(left + right) // 2,
            center_y=(top + bottom) // 2,
            confidence=confidence,
            left=left,
            top=top,
            right=right,
            bottom=bottom,
        )
        if (
            selected_detection is None
            or candidate.confidence > selected_detection.confidence
        ):
            selected_detection = candidate
    return selected_detection


def draw_detection(frame, detection, fps):
    import cv2

    if detection is not None:
        cv2.rectangle(
            frame, (detection.left, detection.top),
            (detection.right, detection.bottom), (50, 220, 80), 2)
        cv2.circle(
            frame, (detection.center_x, detection.center_y), 5, (0, 80, 255), -1)
        label = (
            f'tennis-ball {detection.confidence:.0%} | '
            f'pixel=({detection.center_x}, {detection.center_y})'
        )
        cv2.putText(
            frame, label, (detection.left, max(24, detection.top - 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.58, (50, 220, 80), 2, cv2.LINE_AA)
    else:
        cv2.putText(
            frame, 'tennis-ball: not detected', (16, 32),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 80, 255), 2, cv2.LINE_AA)
    cv2.putText(
        frame, f'FPS: {fps:.1f} | q: quit', (16, frame.shape[0] - 18),
        cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)


def main():
    arguments = parse_arguments()
    model_path = arguments.model.resolve()
    if not model_path.is_file():
        raise SystemExit(f'Model weights do not exist: {model_path}')

    try:
        import cv2
        from ultralytics import YOLO
    except ImportError as error:
        raise SystemExit(
            'Missing dependency: run pip install -r requirements.txt first.') from error

    model = YOLO(str(model_path))
    camera = cv2.VideoCapture(arguments.camera)
    if not camera.isOpened():
        raise SystemExit(f'Cannot open camera index {arguments.camera}.')

    publisher = RosPixelPublisher(arguments.ros_topic) if arguments.ros_topic else None
    previous_time = perf_counter()
    print('Press q in the camera window to quit.')
    try:
        while True:
            success, frame = camera.read()
            if not success:
                raise RuntimeError('Camera frame capture failed.')
            result = model(
                frame, conf=arguments.confidence, imgsz=arguments.imgsz,
                verbose=False)[0]
            detection = choose_detection(result, arguments.class_name)
            current_time = perf_counter()
            fps = 1.0 / max(current_time - previous_time, 1e-6)
            previous_time = current_time
            draw_detection(frame, detection, fps)
            if publisher is not None and detection is not None:
                publisher.publish(detection)
            cv2.imshow('YOLO tennis-ball pixel detector', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        if publisher is not None:
            publisher.close()


if __name__ == '__main__':
    main()
