"""
自定义图形项，用于RRT算法可视化
"""

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath, QRadialGradient, QLinearGradient
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsPathItem


class StartPoint(QGraphicsEllipseItem):
    """起点图形项"""

    def __init__(self, x, y, radius=8):
        """
        初始化起点图形

        参数:
            x, y: 坐标
            radius: 半径
        """
        super().__init__(x - radius, y - radius, 2 * radius, 2 * radius)

        # 创建径向渐变效果
        gradient = QRadialGradient(x, y, radius)
        gradient.setColorAt(0, QColor(0, 230, 0))  # 中心为亮绿色
        gradient.setColorAt(1, QColor(0, 150, 0))  # 边缘为深绿色

        self.setPen(QPen(QColor(0, 80, 0), 2))
        self.setBrush(QBrush(gradient))
        self.setZValue(10)  # 确保在最上层显示


class GoalPoint(QGraphicsEllipseItem):
    """终点图形项"""

    def __init__(self, x, y, radius=8):
        """
        初始化终点图形

        参数:
            x, y: 坐标
            radius: 半径
        """
        super().__init__(x - radius, y - radius, 2 * radius, 2 * radius)

        # 创建径向渐变效果
        gradient = QRadialGradient(x, y, radius)
        gradient.setColorAt(0, QColor(255, 60, 60))  # 中心为亮红色
        gradient.setColorAt(1, QColor(180, 0, 0))    # 边缘为深红色

        self.setPen(QPen(QColor(120, 0, 0), 2))
        self.setBrush(QBrush(gradient))
        self.setZValue(10)  # 确保在最上层显示


class TreeNode(QGraphicsEllipseItem):
    """树节点图形项"""

    def __init__(self, x, y, radius=2.5):
        """
        初始化树节点图形

        参数:
            x, y: 坐标
            radius: 半径
        """
        super().__init__(x - radius, y - radius, 2 * radius, 2 * radius)

        # 使用明亮的蓝色
        node_color = QColor(30, 120, 255)

        self.setPen(QPen(node_color.darker(120), 0.5))
        self.setBrush(QBrush(node_color))
        self.setZValue(5)


class TreeEdge(QGraphicsLineItem):
    """树边图形项"""

    def __init__(self, x1, y1, x2, y2):
        """
        初始化树边图形

        参数:
            x1, y1: 起点坐标
            x2, y2: 终点坐标
        """
        super().__init__(x1, y1, x2, y2)

        # 使用半透明的蓝色
        edge_color = QColor(100, 130, 255, 180)

        pen = QPen(edge_color, 1)
        pen.setStyle(Qt.SolidLine)
        self.setPen(pen)
        self.setZValue(1)


class PathSegment(QGraphicsLineItem):
    """路径段图形项"""

    def __init__(self, x1, y1, x2, y2):
        """
        初始化路径段图形

        参数:
            x1, y1: 起点坐标
            x2, y2: 终点坐标
        """
        super().__init__(x1, y1, x2, y2)

        # 创建更吸引人的路径
        pen = QPen(QColor(255, 30, 30), 2.5, Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        self.setPen(pen)
        self.setZValue(8)


class ObstacleItem:
    """障碍物图形项基类"""

    @staticmethod
    def create_from_obstacle(obstacle):
        """
        根据障碍物对象创建图形项

        参数:
            obstacle: 障碍物对象

        返回:
            item: 图形项
        """
        obstacle_type = obstacle.get_type()

        if obstacle_type == "rectangle":
            x, y, width, height = obstacle.get_boundary()
            item = QGraphicsRectItem(x, y, width, height)

            # 创建线性渐变
            gradient = QLinearGradient(x, y, x + width, y + height)
            gradient.setColorAt(0, QColor(40, 40, 40))    # 顶部为深灰色
            gradient.setColorAt(1, QColor(10, 10, 10))    # 底部为近黑色

            item.setPen(QPen(QColor(50, 50, 50), 1.5))
            item.setBrush(QBrush(gradient))

        elif obstacle_type == "circle":
            center_x, center_y, radius = obstacle.get_boundary()
            item = QGraphicsEllipseItem(center_x - radius, center_y - radius, 2 * radius, 2 * radius)

            # 创建径向渐变
            gradient = QRadialGradient(center_x, center_y, radius)
            gradient.setColorAt(0, QColor(40, 40, 40))    # 中心为深灰色
            gradient.setColorAt(1, QColor(10, 10, 10))    # 边缘为近黑色

            item.setPen(QPen(QColor(50, 50, 50), 1.5))
            item.setBrush(QBrush(gradient))

        elif obstacle_type == "polygon":
            vertices = obstacle.get_boundary()
            path = QPainterPath()
            path.moveTo(vertices[0][0], vertices[0][1])

            for i in range(1, len(vertices)):
                path.lineTo(vertices[i][0], vertices[i][1])

            item = QGraphicsPathItem(path)
            item.setPen(QPen(QColor(50, 50, 50), 1.5))
            item.setBrush(QBrush(QColor(20, 20, 20)))

        else:
            raise ValueError(f"Unknown obstacle type: {obstacle_type}")

        item.setZValue(2)  # 确保障碍物在树和路径下方
        return item