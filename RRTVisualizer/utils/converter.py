"""
数据转换工具，用于处理NumPy数组和Python对象间的转换
"""

import numpy as np


def numpy_to_list(obj):
    """
    递归地将NumPy数组转换为Python列表，使其可用于JSON序列化

    参数:
        obj: 包含NumPy数组的对象（字典、列表、NumPy数组或基本类型）

    返回:
        转换后的对象，所有NumPy数组都转换为普通Python列表
    """
    if isinstance(obj, dict):
        # 处理字典：递归转换每个值
        return {key: numpy_to_list(value) for key, value in obj.items()}
    elif isinstance(obj, list) or isinstance(obj, tuple):
        # 处理列表或元组：递归转换每个元素
        return [numpy_to_list(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        # 转换NumPy数组为Python列表
        return obj.tolist()
    elif hasattr(obj, 'tolist') and callable(getattr(obj, 'tolist')):
        # 处理具有tolist方法的对象
        return obj.tolist()
    else:
        # 返回其他类型的值不变
        return obj


def list_to_numpy(obj):
    """
    递归地将Python列表转换为NumPy数组

    参数:
        obj: 包含列表的对象（字典、列表或基本类型）

    返回:
        转换后的对象，所有适合的列表都转换为NumPy数组
    """
    if isinstance(obj, dict):
        # 处理字典：递归转换每个值
        return {key: list_to_numpy(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        # 检查是否是数值列表
        if all(isinstance(x, (int, float)) for x in obj) or all(isinstance(x, list) for x in obj):
            try:
                return np.array(obj)
            except:
                # 如果无法转换为NumPy数组，递归处理每个元素
                return [list_to_numpy(item) for item in obj]
        else:
            # 混合类型列表，递归处理每个元素
            return [list_to_numpy(item) for item in obj]
    else:
        # 返回其他类型的值不变
        return obj