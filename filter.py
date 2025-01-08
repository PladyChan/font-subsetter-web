def filter_alphanumeric(text):
    # 保留英文字母、数字和标点符号
    return ''.join(char for char in text if (char.isalnum() or char in string.punctuation) and ord(char) < 128)

# 需要导入string模块来使用punctuation
import string

# 测试用例
test_cases = [
    "Hello世界123！@#$",
    "测试ABC123,.",
    "汉字English!混合2023年",
    "!@#$%^&*()",
    "αβγABC123...?"  # 希腊字母会被过滤掉，但标点符号保留
]

for test in test_cases:
    result = filter_alphanumeric(test)
    print(f"原文: {test}")
    print(f"结果: {result}\n") 