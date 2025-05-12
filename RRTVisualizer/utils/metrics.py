"""
性能指标计算工具函数
"""

import numpy as np


def calculate_path_length(path):
    """
    计算路径长度

    参数:
        path: 路径点列表 [[x1, y1], [x2, y2], ...]

    返回:
        length: 路径长度
    """
    if not path or len(path) < 2:
        return 0.0

    length = 0.0
    for i in range(len(path) - 1):
        p1 = np.array(path[i])
        p2 = np.array(path[i + 1])
        length += np.linalg.norm(p2 - p1)

    return length


def calculate_path_smoothness(path):
    """
    计算路径平滑度（角度变化的标准差）

    参数:
        path: 路径点列表 [[x1, y1], [x2, y2], ...]

    返回:
        smoothness: 路径平滑度（角度变化的标准差），值越小越平滑
    """
    if not path or len(path) < 3:
        return 0.0

    # 计算每段路径的方向向量
    vectors = []
    for i in range(len(path) - 1):
        p1 = np.array(path[i])
        p2 = np.array(path[i + 1])
        vec = p2 - p1
        # 归一化
        norm = np.linalg.norm(vec)
        if norm > 1e-6:  # 避免除以零
            vec = vec / norm
        vectors.append(vec)

    # 计算相邻向量之间的角度
    angles = []
    for i in range(len(vectors) - 1):
        v1 = vectors[i]
        v2 = vectors[i + 1]
        # 计算夹角（弧度）
        cos_angle = np.clip(np.dot(v1, v2), -1.0, 1.0)
        angle = np.arccos(cos_angle)
        angles.append(angle)

    # 计算角度变化的标准差
    if angles:
        return np.std(angles)
    else:
        return 0.0