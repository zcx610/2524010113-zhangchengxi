import cv2
import numpy as np

# ===============================
# 1. 图像加载
# ===============================
image_path = "test.jpg"   # 换成你自己的图片路径
img = cv2.imread(image_path)

if img is None:
    raise IOError("无法加载图像，请检查路径是否正确")

# ===============================
# 2. 图像裁剪（示例：中心区域）
# ===============================
h, w = img.shape[:2]
crop_x1 = w // 4
crop_y1 = h // 4
crop_x2 = 3 * w // 4
crop_y2 = 3 * h // 4

cropped_img = img[crop_y1:crop_y2, crop_x1:crop_x2]

# ===============================
# 3. 对比度 & 亮度增强
# 公式：new_img = alpha * img + beta
# alpha: 对比度（>1 增强，<1 减弱）
# beta : 亮度（正值变亮，负值变暗）
# ===============================
alpha = 1.3   # 对比度
beta = 30     # 亮度

adjusted_img = cv2.convertScaleAbs(cropped_img, alpha=alpha, beta=beta)

# ===============================
# 4. 整体高斯模糊
# ===============================
gaussian_blur_img = cv2.GaussianBlur(adjusted_img, (15, 15), 0)

# ===============================
# 5. 人脸检测 + 人脸区域模糊
# ===============================

# 加载 Haar 级联分类器（OpenCV 自带）
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# 转为灰度图（人脸检测要求）
gray = cv2.cvtColor(gaussian_blur_img, cv2.COLOR_BGR2GRAY)

# 检测人脸
faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30, 30)
)

# 对人脸区域进行高斯模糊
result_img = gaussian_blur_img.copy()
for (x, y, fw, fh) in faces:
    face_roi = result_img[y:y + fh, x:x + fw]
    blurred_face = cv2.GaussianBlur(face_roi, (99, 99), 30)
    result_img[y:y + fh, x:x + fw] = blurred_face

    # 可选：画矩形框（调试用）
    cv2.rectangle(result_img, (x, y), (x + fw, y + fh), (0, 255, 0), 2)

# ===============================
# 6. 显示结果
# ===============================
cv2.imshow("Original Image", img)
cv2.imshow("Cropped Image", cropped_img)
cv2.imshow("Brightness & Contrast Adjusted", adjusted_img)
cv2.imshow("Gaussian Blurred", gaussian_blur_img)
cv2.imshow("Face Blurred Result", result_img)

print(f"检测到 {len(faces)} 张人脸")

cv2.waitKey(0)
cv2.destroyAllWindows()