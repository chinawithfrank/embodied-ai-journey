import argparse

import cv2 as cv
import numpy as np


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="使用OpenCV和HSV颜色范围识别绿色小球"
    )

    parser.add_argument(
        "--lower-hsv",
        type=int,
        nargs=3,
        default=[35, 80, 60],
        metavar=("H", "S", "V"),
        help="绿色HSV下限，默认：35 80 60"
    )

    parser.add_argument(
        "--upper-hsv",
        type=int,
        nargs=3,
        default=[85, 255, 255],
        metavar=("H", "S", "V"),
        help="绿色HSV上限，默认：85 255 255"
    )

    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="摄像头编号，默认：0"
    )

    parser.add_argument(
        "--min-area",
        type=float,
        default=500,
        help="最小有效轮廓面积，默认：500"
    )

    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="单个画面的宽度，默认：640"
    )

    parser.add_argument(
        "--height",
        type=int,
        default=360,
        help="单个画面的高度，默认：360"
    )

    return parser.parse_args()


def validate_hsv(lower_hsv, upper_hsv):
    """检查HSV参数是否合法。"""
    hsv_ranges = (
        ("H", 0, 179),
        ("S", 0, 255),
        ("V", 0, 255)
    )

    for index, (name, minimum, maximum) in enumerate(hsv_ranges):
        lower_value = int(lower_hsv[index])
        upper_value = int(upper_hsv[index])

        if not minimum <= lower_value <= maximum:
            raise ValueError(
                f"{name}下限必须位于{minimum}～{maximum}之间，"
                f"当前值为{lower_value}"
            )

        if not minimum <= upper_value <= maximum:
            raise ValueError(
                f"{name}上限必须位于{minimum}～{maximum}之间，"
                f"当前值为{upper_value}"
            )

        if lower_value > upper_value:
            raise ValueError(
                f"{name}下限不能大于上限："
                f"{lower_value} > {upper_value}"
            )


def add_title(image, title):
    """在图像顶部增加标题栏。"""
    result = image.copy()

    cv.rectangle(
        result,
        (0, 0),
        (result.shape[1], 38),
        (0, 0, 0),
        -1
    )

    cv.putText(
        result,
        title,
        (12, 27),
        cv.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv.LINE_AA
    )

    return result


def create_hue_visualization(hsv):
    """将HSV中的H通道转换成便于观察的伪彩色图像。"""
    hue = hsv[:, :, 0]

    hue_8bit = np.uint8(
        hue.astype(np.float32) * 255.0 / 179.0
    )

    return cv.applyColorMap(
        hue_8bit,
        cv.COLORMAP_HSV
    )


def detect_largest_object(
    mask,
    output_image,
    min_area
):
    """
    从二值Mask中寻找面积最大的目标，并在output_image上绘制结果。

    返回：
        found：是否找到有效目标
        center：目标质心像素坐标
        radius：最小外接圆半径
        area：轮廓面积
    """
    contours, _ = cv.findContours(
        mask,
        cv.RETR_EXTERNAL,
        cv.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return False, None, 0.0, 0.0

    largest_contour = max(
        contours,
        key=cv.contourArea
    )

    area = cv.contourArea(largest_contour)

    if area < min_area:
        return False, None, 0.0, area

    # 计算最小外接圆
    (circle_x, circle_y), radius = cv.minEnclosingCircle(
        largest_contour
    )

    # 使用图像矩计算轮廓质心
    moments = cv.moments(largest_contour)

    if moments["m00"] == 0:
        return False, None, radius, area

    center_x = int(
        moments["m10"] / moments["m00"]
    )

    center_y = int(
        moments["m01"] / moments["m00"]
    )

    center = (center_x, center_y)

    # 绘制目标轮廓
    cv.drawContours(
        output_image,
        [largest_contour],
        -1,
        (0, 255, 0),
        2
    )

    # 绘制最小外接圆
    cv.circle(
        output_image,
        (int(circle_x), int(circle_y)),
        int(radius),
        (255, 0, 0),
        2
    )

    # 绘制目标质心
    cv.drawMarker(
        output_image,
        center,
        (0, 255, 255),
        cv.MARKER_CROSS,
        25,
        3
    )

    # 显示像素坐标
    text_x = min(
        center_x + 15,
        output_image.shape[1] - 230
    )

    text_y = max(
        center_y - 15,
        60
    )

    cv.putText(
        output_image,
        f"Pixel: ({center_x}, {center_y})",
        (text_x, text_y),
        cv.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
        cv.LINE_AA
    )

    # 显示面积与半径
    cv.putText(
        output_image,
        f"Area: {area:.0f}",
        (15, output_image.shape[0] - 38),
        cv.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
        cv.LINE_AA
    )

    cv.putText(
        output_image,
        f"Radius: {radius:.1f}px",
        (15, output_image.shape[0] - 12),
        cv.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
        cv.LINE_AA
    )

    return True, center, radius, area


def main():
    args = parse_args()

    lower_green = np.array(
        args.lower_hsv,
        dtype=np.uint8
    )

    upper_green = np.array(
        args.upper_hsv,
        dtype=np.uint8
    )

    validate_hsv(
        lower_green,
        upper_green
    )

    print("绿色小球识别程序已启动")
    print(f"HSV下限：{lower_green.tolist()}")
    print(f"HSV上限：{upper_green.tolist()}")
    print(f"最小轮廓面积：{args.min_area}")
    print("按 M：切换形态学处理前后的Mask")
    print("按 Q 或 Esc：退出程序")

    # 打开摄像头
    cap = cv.VideoCapture(args.camera)

    if not cap.isOpened():
        raise RuntimeError(
            f"无法打开编号为{args.camera}的摄像头"
        )

    # 尝试设置摄像头采集分辨率
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    # 椭圆形结构元素更适合圆形目标
    kernel = cv.getStructuringElement(
        cv.MORPH_ELLIPSE,
        (7, 7)
    )

    # 默认显示形态学处理后的Mask
    show_clean_mask = True

    while True:
        success, frame = cap.read()

        if not success:
            print("无法读取摄像头画面")
            break

        # 统一每一个面板的尺寸，避免拼接时比例不一致
        frame = cv.resize(
            frame,
            (args.width, args.height),
            interpolation=cv.INTER_AREA
        )

        # --------------------------------------------------
        # 第一步：高斯滤波
        # 减弱摄像头噪声以及颜色的局部抖动
        # --------------------------------------------------
        blurred = cv.GaussianBlur(
            frame,
            (7, 7),
            0
        )

        # --------------------------------------------------
        # 第二步：BGR转HSV
        # --------------------------------------------------
        hsv = cv.cvtColor(
            blurred,
            cv.COLOR_BGR2HSV
        )

        # --------------------------------------------------
        # 第三步：HSV阈值分割
        # 范围内的像素变成白色，其余变成黑色
        # --------------------------------------------------
        raw_mask = cv.inRange(
            hsv,
            lower_green,
            upper_green
        )

        # --------------------------------------------------
        # 第四步：形态学处理
        # --------------------------------------------------

        # 开运算：先腐蚀、再膨胀
        # 用来去除目标外部零散的白色噪点
        clean_mask = cv.morphologyEx(
            raw_mask,
            cv.MORPH_OPEN,
            kernel,
            iterations=1
        )

        # 闭运算：先膨胀、再腐蚀
        # 用来填补目标内部的小型黑色空洞
        clean_mask = cv.morphologyEx(
            clean_mask,
            cv.MORPH_CLOSE,
            kernel,
            iterations=2
        )

        # --------------------------------------------------
        # 第五步：轮廓检测
        # --------------------------------------------------
        detection = frame.copy()

        found, center, radius, area = detect_largest_object(
            clean_mask,
            detection,
            args.min_area
        )

        if not found:
            cv.putText(
                detection,
                "Green ball not found",
                (15, args.height - 20),
                cv.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
                cv.LINE_AA
            )

        # --------------------------------------------------
        # 第六步：准备四块显示画面
        # --------------------------------------------------
        hue_visual = create_hue_visualization(hsv)

        if show_clean_mask:
            selected_mask = clean_mask
            mask_title = "Mask - After Morphology"
        else:
            selected_mask = raw_mask
            mask_title = "Mask - Before Morphology"

        mask_bgr = cv.cvtColor(
            selected_mask,
            cv.COLOR_GRAY2BGR
        )

        original_panel = add_title(
            frame,
            "1. Original"
        )

        hsv_panel = add_title(
            hue_visual,
            "2. HSV - Hue"
        )

        mask_panel = add_title(
            mask_bgr,
            f"3. {mask_title}"
        )

        detection_panel = add_title(
            detection,
            "4. Green Ball Detection"
        )

        # --------------------------------------------------
        # 第七步：2×2拼接
        #
        # Original       HSV Hue
        # Mask           Detection
        # --------------------------------------------------
        top_row = np.hstack((
            original_panel,
            hsv_panel
        ))

        bottom_row = np.hstack((
            mask_panel,
            detection_panel
        ))

        dashboard = np.vstack((
            top_row,
            bottom_row
        ))

        cv.imshow(
            "OpenCV Green Ball Detector",
            dashboard
        )

        key = cv.waitKey(1) & 0xFF

        # M键切换形态学处理前后的Mask
        if key == ord("m"):
            show_clean_mask = not show_clean_mask

        # Q或者Esc退出
        if key == ord("q") or key == 27:
            break

    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
