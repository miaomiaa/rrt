"""
障碍物类定义

包含各种形状的障碍物，用于RRT算法中的碰撞检测
"""

import numpy as np
from abc import ABC, abstractmethod


class Obstacle(ABC):
    """障碍物基类"""

    def __init__(self, color='black'):
        """
        初始化障碍物

        参数:
            color: 障碍物的颜色（用于可视化）
        """
        self.color = color

    @abstractmethod
    def is_point_in_obstacle(self, point):
        """
        判断点是否在障碍物内部

        参数:
            point: 点坐标 [x, y]

        返回:
            bool: 是否在障碍物内部
        """
        pass

    @abstractmethod
    def is_line_in_obstacle(self, start, end):
        """
        判断线段是否与障碍物相交

        参数:
            start: 线段起点坐标 [x, y]
            end: 线段终点坐标 [x, y]

        返回:
            bool: 是否与障碍物相交
        """
        pass

    @abstractmethod
    def get_boundary(self):
        """
        获取障碍物的边界

        返回:
            boundary: 障碍物的边界描述（格式取决于障碍物类型）
        """
        pass

    @abstractmethod
    def get_type(self):
        """
        获取障碍物类型

        返回:
            type: 障碍物类型字符串
        """
        pass


class RectangleObstacle(Obstacle):
    """矩形障碍物"""

    def __init__(self, x, y, width, height, color='black'):
        """
        初始化矩形障碍物

        参数:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度
            color: 障碍物的颜色
        """
        super().__init__(color)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def is_point_in_obstacle(self, point):
        """
        判断点是否在矩形内部

        参数:
            point: 点坐标 [x, y]

        返回:
            bool: 是否在矩形内部
        """
        return (self.x <= point[0] <= self.x + self.width and
                self.y <= point[1] <= self.y + self.height)

    def is_line_in_obstacle(self, start, end):
        """
        判断线段是否与矩形相交
        使用分离轴定理

        参数:
            start: 线段起点坐标 [x, y]
            end: 线段终点坐标 [x, y]

        返回:
            bool: 是否与矩形相交
        """
        # 如果起点或终点在矩形内部，则相交
        if self.is_point_in_obstacle(start) or self.is_point_in_obstacle(end):
            return True

        # 如果线段在矩形的某一边外完全投影，则不相交
        if (start[0] < self.x and end[0] < self.x) or \
                (start[0] > self.x + self.width and end[0] > self.x + self.width) or \
                (start[1] < self.y and end[1] < self.y) or \
                (start[1] > self.y + self.height and end[1] > self.y + self.height):
            return False

        # 检查线段是否与矩形的边相交
        # 矩形的四条边
        rectangle_edges = [
            ([self.x, self.y], [self.x + self.width, self.y]),  # 上边
            ([self.x, self.y], [self.x, self.y + self.height]),  # 左边
            ([self.x + self.width, self.y], [self.x + self.width, self.y + self.height]),  # 右边
            ([self.x, self.y + self.height], [self.x + self.width, self.y + self.height])  # 下边
        ]

        # 检查线段是否与矩形的任一边相交
        for edge in rectangle_edges:
            if self._line_intersection(start, end, edge[0], edge[1]):
                return True

        return False

    def _line_intersection(self, line1_start, line1_end, line2_start, line2_end):
        """
        检查两条线段是否相交

        参数:
            line1_start, line1_end: 第一条线段的端点
            line2_start, line2_end: 第二条线段的端点

        返回:
            bool: 是否相交
        """
        # 计算方向向量
        v1 = np.array(line1_end) - np.array(line1_start)
        v2 = np.array(line2_end) - np.array(line2_start)

        # 计算叉积
        cross_product = np.cross(v1, v2)

        # 如果叉积为0，则两线段平行
        if abs(cross_product) < 1e-10:
            return False

        # 计算参数t1和t2
        v = np.array(line2_start) - np.array(line1_start)
        t1 = np.cross(v, v2) / cross_product
        t2 = np.cross(v, v1) / cross_product

        # 检查t1和t2是否在[0, 1]范围内
        return 0 <= t1 <= 1 and 0 <= t2 <= 1

    def get_boundary(self):
        """
        获取矩形的边界

        返回:
            (x, y, width, height): 矩形的左上角坐标和宽高
        """
        return (self.x, self.y, self.width, self.height)

    def get_type(self):
        """返回障碍物类型"""
        return "rectangle"


class CircleObstacle(Obstacle):
    """圆形障碍物"""

    def __init__(self, center_x, center_y, radius, color='black'):
        """
        初始化圆形障碍物

        参数:
            center_x: 圆心x坐标
            center_y: 圆心y坐标
            radius: 半径
            color: 障碍物的颜色
        """
        super().__init__(color)
        self.center = np.array([center_x, center_y])
        self.radius = radius

    def is_point_in_obstacle(self, point):
        """
        判断点是否在圆内部

        参数:
            point: 点坐标 [x, y]

        返回:
            bool: 是否在圆内部
        """
        return np.linalg.norm(np.array(point) - self.center) <= self.radius

    def is_line_in_obstacle(self, start, end):
        """
        判断线段是否与圆相交

        参数:
            start: 线段起点坐标 [x, y]
            end: 线段终点坐标 [x, y]

        返回:
            bool: 是否与圆相交
        """
        # 如果起点或终点在圆内部，则相交
        if self.is_point_in_obstacle(start) or self.is_point_in_obstacle(end):
            return True

        # 计算线段的方向向量
        line_dir = np.array(end) - np.array(start)
        line_length = np.linalg.norm(line_dir)
        line_dir = line_dir / line_length  # 单位化

        # 计算从线段起点到圆心的向量
        start_to_center = self.center - np.array(start)

        # 计算圆心到线段的最短距离
        projection = np.dot(start_to_center, line_dir)

        # 如果投影在线段外部，则计算圆心到线段端点的距离
        if projection < 0:
            distance = np.linalg.norm(start_to_center)
        elif projection > line_length:
            distance = np.linalg.norm(self.center - np.array(end))
        else:
            # 计算圆心到线段的垂直距离
            distance = np.linalg.norm(start_to_center - projection * line_dir)

        # 如果距离小于等于半径，则相交
        return distance <= self.radius

    def get_boundary(self):
        """
        获取圆的边界

        返回:
            (center_x, center_y, radius): 圆心坐标和半径
        """
        return (self.center[0], self.center[1], self.radius)

    def get_type(self):
        """返回障碍物类型"""
        return "circle"


class PolygonObstacle(Obstacle):
    """多边形障碍物"""

    def __init__(self, vertices, color='black'):
        """
        初始化多边形障碍物

        参数:
            vertices: 多边形的顶点坐标列表 [[x1, y1], [x2, y2], ...]
            color: 障碍物的颜色
        """
        super().__init__(color)
        self.vertices = np.array(vertices)

        # 确保多边形是闭合的
        if not np.array_equal(self.vertices[0], self.vertices[-1]):
            self.vertices = np.vstack([self.vertices, self.vertices[0]])

    def is_point_in_obstacle(self, point):
        """
        判断点是否在多边形内部
        使用射线法（ray casting algorithm）

        参数:
            point: 点坐标 [x, y]

        返回:
            bool: 是否在多边形内部
        """
        point = np.array(point)
        n = len(self.vertices) - 1  # 减去闭合点
        inside = False

        for i in range(n):
            v1 = self.vertices[i]
            v2 = self.vertices[i + 1]

            # 检查点是否在边的y范围内
            if ((v1[1] <= point[1] < v2[1]) or (v2[1] <= point[1] < v1[1])):
                # 计算边与水平射线相交的x坐标
                if v1[1] != v2[1]:  # 非水平边
                    x_intersect = v1[0] + (point[1] - v1[1]) * (v2[0] - v1[0]) / (v2[1] - v1[1])

                    # 如果交点在点的右侧，则切换内外状态
                    if x_intersect > point[0]:
                        inside = not inside

        return inside

    def is_line_in_obstacle(self, start, end):
        """
        判断线段是否与多边形相交

        参数:
            start: 线段起点坐标 [x, y]
            end: 线段终点坐标 [x, y]

        返回:
            bool: 是否与多边形相交
        """
        # 如果起点或终点在多边形内部，则相交
        if self.is_point_in_obstacle(start) or self.is_point_in_obstacle(end):
            return True

        # 检查线段是否与多边形的任一边相交
        n = len(self.vertices) - 1  # 减去闭合点
        for i in range(n):
            v1 = self.vertices[i]
            v2 = self.vertices[i + 1]

            if self._line_intersection(start, end, v1, v2):
                return True

        return False

    def _line_intersection(self, line1_start, line1_end, line2_start, line2_end):
        """
        检查两条线段是否相交

        参数:
            line1_start, line1_end: 第一条线段的端点
            line2_start, line2_end: 第二条线段的端点

        返回:
            bool: 是否相交
        """
        # 计算方向向量
        v1 = np.array(line1_end) - np.array(line1_start)
        v2 = np.array(line2_end) - np.array(line2_start)

        # 计算叉积
        cross_product = np.cross(v1, v2)

        # 如果叉积为0，则两线段平行
        if abs(cross_product) < 1e-10:
            return False

        # 计算参数t1和t2
        v = np.array(line2_start) - np.array(line1_start)
        t1 = np.cross(v, v2) / cross_product
        t2 = np.cross(v, v1) / cross_product

        # 检查t1和t2是否在[0, 1]范围内
        return 0 <= t1 <= 1 and 0 <= t2 <= 1

    def get_boundary(self):
        """
        获取多边形的边界

        返回:
            vertices: 多边形的顶点坐标列表
        """
        return self.vertices.tolist()

    def get_type(self):
        """返回障碍物类型"""
        return "polygon"