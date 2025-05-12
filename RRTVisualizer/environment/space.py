"""
配置空间类定义

配置空间包含机器人的运动范围和障碍物信息，用于RRT算法的碰撞检测和采样
"""

import numpy as np
from .obstacles import Obstacle


class ConfigurationSpace:
    """配置空间类"""

    def __init__(self, width, height, obstacles=None):
        """
        初始化配置空间

        参数:
            width: 空间宽度
            height: 空间高度
            obstacles: 障碍物列表
        """
        self.width = width
        self.height = height
        self.obstacles = obstacles or []

        # 空间边界
        self.bounds = {
            'x_min': 0,
            'x_max': width,
            'y_min': 0,
            'y_max': height
        }

    def add_obstacle(self, obstacle):
        """
        添加障碍物

        参数:
            obstacle: 障碍物对象
        """
        if isinstance(obstacle, Obstacle):
            self.obstacles.append(obstacle)
        else:
            raise TypeError("obstacle must be an instance of Obstacle")

    def remove_obstacle(self, index):
        """
        移除障碍物

        参数:
            index: 障碍物索引
        """
        if 0 <= index < len(self.obstacles):
            del self.obstacles[index]
        else:
            raise IndexError("obstacle index out of range")

    def clear_obstacles(self):
        """清除所有障碍物"""
        self.obstacles = []

    def is_in_bounds(self, point):
        """
        判断点是否在配置空间边界内

        参数:
            point: 点坐标 [x, y]

        返回:
            bool: 是否在边界内
        """
        return (self.bounds['x_min'] <= point[0] <= self.bounds['x_max'] and
                self.bounds['y_min'] <= point[1] <= self.bounds['y_max'])

    def is_collision_free(self, from_point, to_point):
        """
        判断从from_point到to_point的路径是否无碰撞

        参数:
            from_point: 起始点
            to_point: 终点

        返回:
            bool: 是否无碰撞
        """
        # 检查起点和终点是否在边界内
        if not self.is_in_bounds(from_point) or not self.is_in_bounds(to_point):
            return False

        # 检查路径是否与任何障碍物相交
        for obstacle in self.obstacles:
            if obstacle.is_line_in_obstacle(from_point, to_point):
                return False

        return True

    def sample(self):
        """
        在配置空间内随机采样一个点

        返回:
            point: 采样点坐标 [x, y]
        """
        # 在边界内均匀采样
        x = np.random.uniform(self.bounds['x_min'], self.bounds['x_max'])
        y = np.random.uniform(self.bounds['y_min'], self.bounds['y_max'])

        return np.array([x, y])

    def sample_free(self, max_attempts=100):
        """
        在配置空间内随机采样一个无碰撞的点

        参数:
            max_attempts: 最大尝试次数

        返回:
            point: 采样点坐标 [x, y]，如果找不到无碰撞点则返回None
        """
        for _ in range(max_attempts):
            point = self.sample()
            collision = False

            # 检查点是否在任何障碍物内部
            for obstacle in self.obstacles:
                if obstacle.is_point_in_obstacle(point):
                    collision = True
                    break

            if not collision:
                return point

        return None  # 找不到无碰撞点

    def get_obstacles(self):
        """
        获取所有障碍物

        返回:
            obstacles: 障碍物列表
        """
        return self.obstacles

    def get_bounds(self):
        """
        获取配置空间边界

        返回:
            bounds: 边界字典
        """
        return self.bounds