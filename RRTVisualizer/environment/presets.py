"""
预设场景模块
包含常用测试场景的定义
"""

from .obstacles import RectangleObstacle, CircleObstacle
from .space import ConfigurationSpace


class ScenePreset:
    """场景预设基类"""

    def __init__(self, name, description, width=800, height=600):
        """
        初始化场景预设

        参数:
            name: 场景名称
            description: 场景描述
            width: 场景宽度
            height: 场景高度
        """
        self.name = name
        self.description = description
        self.width = width
        self.height = height
        self.suggested_start = [50, 50]
        self.suggested_goal = [width - 50, height - 50]

    def create_space(self):
        """创建狭窄通道场景"""
        space = super().create_space()

        # 计算通道位置（在场景中央）
        wall_y = self.height / 2
        passage_center = self.width / 2
        passage_width = 50  # 通道宽度
        wall_width = (self.width - passage_width) / 2

        # 添加上下两堵墙，中间留出通道
        space.add_obstacle(RectangleObstacle(0, wall_y - 10, passage_center - passage_width / 2, 20))
        space.add_obstacle(RectangleObstacle(passage_center + passage_width / 2, wall_y - 10,
                                             self.width - (passage_center + passage_width / 2), 20))

        return space

    def get_metadata(self):
        """
        获取场景元数据

        返回:
            dict: 场景元数据字典
        """
        return {
            'name': self.name,
            'description': self.description,
            'width': self.width,
            'height': self.height,
            'suggested_start': self.suggested_start,
            'suggested_goal': self.suggested_goal
        }


class EmptyScene(ScenePreset):
    """空场景"""

    def __init__(self, width=800, height=600):
        super().__init__("空场景", "一个没有障碍物的空场景，适合基本算法测试", width, height)


class NarrowPassageScene(ScenePreset):
    """狭窄通道场景"""

    def __init__(self, width=800, height=600):
        super().__init__("狭窄通道", "包含一个狭窄通道的场景，测试算法在受限空间的表现", width, height)
        self.passage_width = 50  # 通道宽度

    def create_space(self):
        """创建狭窄通道场景"""
        space = super().create_space()

        # 计算通道位置（在场景中央）
        wall_y = self.height / 2
        passage_x = self.width / 2
        wall_width = self.width / 2 - self.passage_width / 2

        # 添加上下两堵墙，中间留出通道
        space.add_obstacle(RectangleObstacle(0, wall_y - 10, wall_width, 20))
        space.add_obstacle(RectangleObstacle(passage_x + self.passage_width / 2, wall_y - 10, wall_width, 20))

        # 更新建议的起点和终点位置（分别在通道两端）
        self.suggested_start = [50, self.height / 2]
        self.suggested_goal = [self.width - 50, self.height / 2]

        return space


class MazeScene(ScenePreset):
    """迷宫场景"""

    def __init__(self, width=800, height=600):
        super().__init__("迷宫", "一个简单的迷宫场景，测试算法的探索能力", width, height)

    def create_space(self):
        """创建迷宫场景"""
        space = super().create_space()

        wall_thickness = 20
        # 外墙
        space.add_obstacle(RectangleObstacle(0, 0, self.width, wall_thickness))  # 上墙
        space.add_obstacle(RectangleObstacle(0, self.height - wall_thickness, self.width, wall_thickness))  # 下墙
        space.add_obstacle(RectangleObstacle(0, 0, wall_thickness, self.height))  # 左墙
        space.add_obstacle(RectangleObstacle(self.width - wall_thickness, 0, wall_thickness, self.height))  # 右墙

        # 迷宫内部墙壁
        corridors = [
            # 横向墙
            [100, 100, 400, wall_thickness],
            [300, 200, 400, wall_thickness],
            [100, 300, 300, wall_thickness],
            [500, 300, 200, wall_thickness],
            [200, 400, 500, wall_thickness],
            [100, 500, 300, wall_thickness],
            # 纵向墙
            [200, 100, wall_thickness, 100],
            [400, 100, wall_thickness, 100],
            [200, 200, wall_thickness, 100],
            [600, 200, wall_thickness, 200],
            [300, 400, wall_thickness, 100],
            [500, 400, wall_thickness, 100],
        ]

        for x, y, w, h in corridors:
            space.add_obstacle(RectangleObstacle(x, y, w, h))

        # 更新建议的起点和终点
        self.suggested_start = [50, 50]
        self.suggested_goal = [self.width - 50, self.height - 50]

        return space


class ObstacleFieldScene(ScenePreset):
    """随机障碍物场景"""

    def __init__(self, width=800, height=600, num_obstacles=20):
        super().__init__("障碍物场", "随机分布的圆形障碍物场景，测试算法的避障能力", width, height)
        self.num_obstacles = num_obstacles

    def create_space(self):
        """创建随机障碍物场景"""
        import random
        space = super().create_space()

        # 设置随机数种子以保持一致性
        random.seed(42)

        # 添加随机圆形障碍物
        min_radius = 20
        max_radius = 50

        for _ in range(self.num_obstacles):
            radius = random.uniform(min_radius, max_radius)
            x = random.uniform(radius, self.width - radius)
            y = random.uniform(radius, self.height - radius)

            # 确保起点和终点附近没有障碍物
            start_dist = ((x - self.suggested_start[0]) ** 2 + (y - self.suggested_start[1]) ** 2) ** 0.5
            goal_dist = ((x - self.suggested_goal[0]) ** 2 + (y - self.suggested_goal[1]) ** 2) ** 0.5

            if start_dist > radius + 50 and goal_dist > radius + 50:
                space.add_obstacle(CircleObstacle(x, y, radius))

        return space


class SpiraleScene(ScenePreset):
    """螺旋障碍场景"""

    def __init__(self, width=800, height=600):
        super().__init__("螺旋迷宫", "螺旋形状的障碍物布局，测试算法穿越复杂结构的能力", width, height)

    def create_space(self):
        """创建螺旋障碍场景"""
        space = super().create_space()

        center_x = self.width / 2
        center_y = self.height / 2

        wall_thickness = 20
        spiral_spacing = 60  # 螺旋间距

        # 创建螺旋墙壁
        for i in range(6):  # 螺旋圈数
            radius = 100 + i * spiral_spacing

            if i % 2 == 0:
                # 顶部开口
                space.add_obstacle(RectangleObstacle(
                    center_x - radius, center_y - radius,
                    2 * radius - wall_thickness, wall_thickness
                ))
                # 右侧墙
                space.add_obstacle(RectangleObstacle(
                    center_x + radius - wall_thickness, center_y - radius,
                    wall_thickness, 2 * radius
                ))
                # 底部墙
                space.add_obstacle(RectangleObstacle(
                    center_x - radius, center_y + radius - wall_thickness,
                    2 * radius, wall_thickness
                ))
                # 左侧开口
            else:
                # 顶部墙
                space.add_obstacle(RectangleObstacle(
                    center_x - radius, center_y - radius,
                    2 * radius, wall_thickness
                ))
                # 右侧开口
                # 底部墙
                space.add_obstacle(RectangleObstacle(
                    center_x - radius, center_y + radius - wall_thickness,
                    2 * radius - wall_thickness, wall_thickness
                ))
                # 左侧墙
                space.add_obstacle(RectangleObstacle(
                    center_x - radius, center_y - radius,
                    wall_thickness, 2 * radius
                ))

        # 更新建议的起点和终点
        self.suggested_start = [center_x, center_y]
        self.suggested_goal = [center_x - 300, center_y - 300]

        return space


class BugtrapScene(ScenePreset):
    """捕虫器场景"""

    def __init__(self, width=800, height=600):
        super().__init__("捕虫器", "包含捕虫器结构的场景，测试算法是否会陷入局部最优", width, height)

    def create_space(self):
        """创建捕虫器场景"""
        space = super().create_space()

        trap_x = self.width / 2
        trap_y = self.height / 2
        trap_width = 200
        trap_height = 200
        wall_thickness = 20

        # 创建U形捕虫器
        # 左墙
        space.add_obstacle(RectangleObstacle(
            trap_x - trap_width / 2, trap_y - trap_height / 2,
            wall_thickness, trap_height
        ))
        # 底墙
        space.add_obstacle(RectangleObstacle(
            trap_x - trap_width / 2, trap_y + trap_height / 2 - wall_thickness,
            trap_width, wall_thickness
        ))
        # 右墙
        space.add_obstacle(RectangleObstacle(
            trap_x + trap_width / 2 - wall_thickness, trap_y - trap_height / 2,
            wall_thickness, trap_height
        ))

        # 更新建议的起点和终点
        self.suggested_start = [trap_x, trap_y]  # 起点在捕虫器内部
        self.suggested_goal = [trap_x, trap_y - trap_height]  # 终点在捕虫器外部

        return space


# 场景预设列表
PRESETS = {
    "empty": EmptyScene(),
    "narrow_passage": NarrowPassageScene(),
    "maze": MazeScene(),
    "obstacle_field": ObstacleFieldScene(),
    "spiral": SpiraleScene(),
    "bugtrap": BugtrapScene()
}