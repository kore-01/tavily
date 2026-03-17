import ddddocr

# 初始化识别器（会自动加载极小的ONNX模型）
ocr = ddddocr.DdddOcr(beta=True)
# 读取图片并识别
with open("test.jpg", 'rb') as f:
    result = ocr.classification(f.read())

print("识别结果:", result)