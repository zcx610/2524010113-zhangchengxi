"""
augment.py
===========
为红绿灯识别任务构建受干扰数据集，验证算法鲁棒性。

干扰类型：
  1. 阳光反光   —— 在灯箱区域叠加高强度高斯光斑
  2. 夜晚灯光   —— 降低整体亮度 + 添加随机高斯噪点
  3. 红色车尾灯误检 —— 在灯箱左侧添加红色圆形色块
  4. 绿色广告牌误检 —— 在灯箱右侧添加绿色矩形色块
  5. 摄像头抖动   —— 对整图做随机仿射变换（平移 + 微小旋转）

输出目录结构：
  augmented/
    sunlight/      ← 阳光反光
    night/         ← 夜晚灯光
    red_car/       ← 红色车尾灯
    green_sign/    ← 绿色广告牌
    jitter/        ← 摄像头抖动
    mixed/         ← 多种干扰叠加

每张增强图文件名格式：原文件名_干扰类型.jpg
"""

import cv2
import numpy as np
import glob
import os
import random

# ================= 路径配置 =================
INPUT_DIR ="input"
AUG_DIR = "augmented"
os.makedirs(AUG_DIR, exist_ok=True)

# 子目录
SUB = {
    "sunlight":  "sunlight",
    "night":     "night",
    "red_car":   "red_car",
    "green_sign":"green_sign",
    "jitter":    "jitter",
    "mixed":     "mixed",
}
for s in SUB.values():
    os.makedirs(os.path.join(AUG_DIR, s), exist_ok=True)

# ROI（与主程序一致）
ROI = (328, 270, 508, 114)

# 随机种子（保证可复现）
random.seed(42)
np.random.seed(42)

# ================= 工具函数 =================
def load_images(folder):
    paths = sorted(glob.glob(os.path.join(folder, "*.*")))
    return [p for p in paths if p.lower().endswith(('.png','.jpg','.jpeg','.bmp'))]

def get_roi(img):
    x, y, w, h = ROI
    x = max(0, min(x, img.shape[1]-1))
    y = max(0, min(y, img.shape[0]-1))
    w = min(w, img.shape[1] - x)
    h = min(h, img.shape[0] - y)
    return img[y:y+h, x:x+w].copy(), (x, y, w, h)

def paste_back(img, roi_img, box):
    x, y, w, h = box
    img[y:y+h, x:x+w] = roi_img
    return img

# ================= 1. 阳光反光 =================
def add_sunlight(img):
    """在灯箱区域叠加1~3个高强度高斯光斑，模拟阳光直射反光"""
    result = img.copy()
    roi, box = get_roi(result)
    rx, ry, rw, rh = box

    n_spots = random.randint(1, 3)
    overlay = roi.copy()
    for _ in range(n_spots):
        cx = random.randint(rw//4, 3*rw//4)
        cy = random.randint(rh//4, 3*rh//4)
        radius = random.randint(15, 45)
        # 光斑中心亮度 240~255
        brightness = random.randint(240, 255)
        cv2.circle(overlay, (cx, cy), radius, (brightness, brightness, brightness), -1)
        # 外圈柔光
        cv2.circle(overlay, (cx, cy), radius*2, (brightness//2, brightness//2, brightness//2), -1)

    # 混合
    blended = cv2.addWeighted(roi, 0.6, overlay, 0.4, 0)
    paste_back(result, blended, box)
    return result

# ================= 2. 夜晚灯光 =================
def add_night(img):
    """整体亮度降低 + 随机高斯噪点，模拟夜间低照度"""
    # 降低亮度到 25%~45%
    factor = random.uniform(0.25, 0.45)
    dark = (img.astype(np.float32) * factor).clip(0, 255).astype(np.uint8)

    # 添加高斯噪点
    noise = np.random.normal(0, random.randint(8, 18), dark.shape).astype(np.float32)
    noisy = (dark.astype(np.float32) + noise).clip(0, 255).astype(np.uint8)

    # 轻微模糊（模拟夜间镜头散焦）
    blurred = cv2.GaussianBlur(noisy, (3,3), 0)
    return blurred

# ================= 3. 红色车尾灯误检 =================
def add_red_tail_light(img):
    """在灯箱左侧外部区域添加红色圆形色块，模拟车尾灯"""
    result = img.copy()
    h, w = result.shape[:2]

    # 在灯箱左侧 50~200 像素范围内随机放 1~2 个红圆
    n = random.randint(1, 2)
    for _ in range(n):
        cx = random.randint(max(0, ROI[0]-200), max(1, ROI[0]-50))
        cy = random.randint(ROI[1], ROI[1]+ROI[3])
        r  = random.randint(8, 20)
        color = (0, 0, random.randint(200, 255))  # 纯红 BGR
        cv2.circle(result, (cx, cy), r, color, -1)
        # 加一点光晕
        cv2.circle(result, (cx, cy), r+4, (0, 0, 180), 2)
    return result

# ================= 4. 绿色广告牌误检 =================
def add_green_sign(img):
    """在灯箱右侧外部区域添加绿色矩形，模拟广告牌"""
    result = img.copy()
    h, w = result.shape[:2]

    n = random.randint(1, 2)
    for _ in range(n):
        # 灯箱右侧
        rx = random.randint(ROI[0]+ROI[2]+20, min(w-60, ROI[0]+ROI[2]+200))
        ry = random.randint(max(0, ROI[1]-40), ROI[1]+ROI[3])
        rw = random.randint(40, 100)
        rh = random.randint(20, 60)
        color = (0, random.randint(160, 220), 0)  # 绿色 BGR
        cv2.rectangle(result, (rx, ry), (rx+rw, ry+rh), color, -1)
        # 边框
        cv2.rectangle(result, (rx, ry), (rx+rw, ry+rh), (0, 180, 0), 2)
    return result

# ================= 5. 摄像头抖动 =================
def add_jitter(img):
    """随机仿射变换：平移 + 微小旋转 + 轻微缩放"""
    h, w = img.shape[:2]
    center = (w//2, h//2)

    # 平移 -15 ~ +15 像素
    tx = random.randint(-15, 15)
    ty = random.randint(-10, 10)
    # 旋转 -4° ~ +4°
    angle = random.uniform(-4, 4)
    # 缩放 0.95 ~ 1.05
    scale = random.uniform(0.95, 1.05)

    M = cv2.getRotationMatrix2D(center, angle, scale)
    M[0,2] += tx
    M[1,2] += ty

    jittered = cv2.warpAffine(img, M, (w, h),
                               flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT,
                               borderValue=(128,128,128))
    return jittered

# ================= 6. 混合干扰 =================
def add_mixed(img):
    """叠加多种干扰：夜晚 + 反光 + 抖动"""
    img = add_night(img)
    img = add_sunlight(img)
    img = add_jitter(img)
    return img

# ================= 主函数 =================
def main():
    images = load_images(INPUT_DIR)
    if not images:
        print(f"❌ {INPUT_DIR} 中未找到图片")
        return

    print(f"找到 {len(images)} 张原始图片\n")

    augmenters = [
        ("sunlight",   add_sunlight,   "阳光反光"),
        ("night",      add_night,      "夜晚灯光"),
        ("red_car",    add_red_tail_light, "红色车尾灯"),
        ("green_sign", add_green_sign, "绿色广告牌"),
        ("jitter",     add_jitter,     "摄像头抖动"),
        ("mixed",      add_mixed,      "混合干扰"),
    ]

    for path in images:
        base = os.path.basename(path)
        name, ext = os.path.splitext(base)
        img = cv2.imread(path)
        if img is None:
            print(f"  ❌ 无法读取 {base}")
            continue

        for tag, func, desc in augmenters:
            augmented = func(img)
            out_name = f"{name}_{tag}{ext}"
            out_path = os.path.join(AUG_DIR, tag, out_name)
            cv2.imwrite(out_path, augmented)
            print(f"  ✅ {desc:10s} → {out_path}")

    print("\n🎉 数据增强完成！")
    print(f"共生成 {len(images) * len(augmenters)} 张干扰图片")
    print(f"输出目录: {AUG_DIR}/")

if __name__ == "__main__":
    main()
