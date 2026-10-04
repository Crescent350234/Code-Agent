"""示例目标文件：供 Agent 审查 / 解释 / 生成测试使用。

该文件故意保留若干常见代码问题（无类型注解、缺乏错误处理、
边界未校验、魔法数字等），便于演示代码审查 Agent 的发现能力。
"""


def divide(a, b):
    # 问题：未处理 b == 0 的除零异常；参数无类型注解
    return a / b


def find_max(nums):
    # 问题：未处理空列表；使用魔法数字
    max_val = nums[0]
    for n in nums:
        if n > max_val:
            max_val = n
    return max_val


def parse_config(text):
    # 问题：未做格式校验，split 行为依赖输入
    result = {}
    for line in text.splitlines():
        key, value = line.split("=")
        result[key.strip()] = value.strip()
    return result


if __name__ == "__main__":
    print(divide(10, 2))
    print(find_max([3, 9, 1, 7]))
    print(parse_config("host=localhost\nport=8080"))
