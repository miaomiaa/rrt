"""
结果导出工具函数
"""

import csv
import json
import os
from datetime import datetime


def export_to_csv(details, path, file_path):
    """
    将规划结果导出为CSV文件

    参数:
        details: 算法详细信息字典
        path: 规划路径点列表
        file_path: 输出文件路径

    返回:
        bool: 是否成功导出
    """
    try:
        with open(file_path, 'w', newline='') as csvfile:
            # 创建CSV写入器
            csv_writer = csv.writer(csvfile)

            # 写入算法信息
            csv_writer.writerow(['# Algorithm Information'])
            for key, value in details.items():
                csv_writer.writerow([key, value])

            # 空行分隔
            csv_writer.writerow([])

            # 写入路径点
            csv_writer.writerow(['# Path Points (x, y)'])
            csv_writer.writerow(['x', 'y'])
            for point in path:
                csv_writer.writerow(point)

        return True
    except Exception as e:
        print(f"Export to CSV failed: {str(e)}")
        return False


def export_to_image(scene, file_path):
    """
    将场景导出为图片

    参数:
        scene: QGraphicsScene对象
        file_path: 输出文件路径

    返回:
        bool: 是否成功导出
    """
    from PyQt5.QtCore import QRectF
    from PyQt5.QtGui import QImage, QPainter

    try:
        # 获取场景矩形
        rect = scene.sceneRect()

        # 创建图片
        image = QImage(
            int(rect.width()),
            int(rect.height()),
            QImage.Format_ARGB32
        )
        image.fill(0xFFFFFFFF)  # 白色背景

        # 创建绘制器
        painter = QPainter(image)

        # 渲染场景到图片
        scene.render(painter, QRectF(), rect)

        # 结束绘制
        painter.end()

        # 保存图片
        image.save(file_path)

        return True
    except Exception as e:
        print(f"Export to image failed: {str(e)}")
        return False


def export_to_json(details, path, file_path):
    """
    将规划结果导出为JSON文件

    参数:
        details: 算法详细信息字典
        path: 规划路径点列表
        file_path: 输出文件路径

    返回:
        bool: 是否成功导出
    """
    try:
        # 构建数据
        data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'algorithm_details': details,
            'path': [point.tolist() if hasattr(point, 'tolist') else point for point in path]
        }

        # 写入JSON文件
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        return True
    except Exception as e:
        print(f"Export to JSON failed: {str(e)}")
        return False