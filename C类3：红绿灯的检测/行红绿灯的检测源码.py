import cv2
import numpy as np

def preprocess_image(image_path):
    """
    读取图片并进行鲁棒预处理，提取红色尾灯候选区域
    """
    # ---------- 1. 读取图像 ----------
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError("图片路径错误，请检查 image_path")

    # ---------- 2. 颜色空间转换 ----------
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # ---------- 3. 红色阈值分割 ----------
    # 红色在 HSV 中分布在两个区间
    lower_red1 = np.array([0, 70, 80])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([160, 70, 80])
    upper_red2 = np.array([179, 255, 255])

    mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask_red1, mask_red2)

    # ---------- 4. 抑制绿色广告牌 ----------
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # 从红色掩膜中剔除绿色区域
    red_mask = cv2.bitwise_and(red_mask, cv2.bitwise_not(green_mask))

    # ---------- 5. 抑制阳光反光 & 过曝 ----------
    # 限制亮度 V，避免强反光和夜间大灯过曝
    lower_v = np.array([0, 0, 80])
    upper_v = np.array([179, 255, 240])
    brightness_mask = cv2.inRange(hsv, lower_v, upper_v)

    red_mask = cv2.bitwise_and(red_mask, brightness_mask)

    # ---------- 6. 形态学处理（抗抖动 & 噪声） ----------
    kernel = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)   # 去噪
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)  # 补洞

    # ---------- 7. 轮廓提取 + 几何约束 ----------
    contours, _ = cv2.findContours(
        red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    result_img = img.copy()
    detected_boxes = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 120:  # 过滤小噪声点
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h + 1e-5)

        # 尾灯一般为横向椭圆/矩形
        if not (0.6 < aspect_ratio < 3.0):
            continue

        detected_boxes.append((x, y, w, h))
        cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            result_img,
            "Red Light",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )

    return img, red_mask, result_img, detected_boxes


def main():
    # ====== 在这里修改你的图片路径 ======
    image_path = r"./test.jpg"

    original, mask, result, boxes = preprocess_image(image_path)

    print(f"检测到候选区域数量: {len(boxes)}")

    cv2.imshow("Original Image", original)
    cv2.imshow("Red Mask", mask)
    cv2.imshow("Detection Result", result)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()