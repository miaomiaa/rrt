"""
基础RRT (Rapidly-exploring Random Tree)算法实现
"""

import numpy as np
import time
from environment.space import ConfigurationSpace


class BaseRRT:
    """基础RRT算法实现类"""

    def __init__(self, start, goal, config_space, step_size=0.5, goal_sample_rate=0.05, max_iter=1000):
        """
        初始化RRT规划器

        参数:
            start: 起始点坐标 [x, y]
            goal: 目标点坐标 [x, y]
            config_space: 配置空间对象
            step_size: 扩展步长
            goal_sample_rate: 采样目标点的概率
            max_iter: 最大迭代次数
        """
        # 确保起点和终点是NumPy数组
        self.start = np.array(start) if not isinstance(start, np.ndarray) else start
        self.goal = np.array(goal) if not isinstance(goal, np.ndarray) else goal
        self.config_space = config_space
        self.step_size = step_size
        self.goal_sample_rate = goal_sample_rate
        self.max_iter = max_iter

        # 树的节点和边
        self.vertices = [self.start]  # 节点列表
        self.edges = []  # 边列表 [(parent_idx, child_idx), ...]
        self.parents = {0: None}  # 父节点索引字典

        # 记录规划过程的数据，用于可视化和分析
        self.planning_time = 0
        self.iterations = 0
        self.path = []
        self.path_length = 0
        self.success = False
        self.expansion_history = []  # 记录每次扩展的节点，用于可视化

    def reset(self):
        """重置规划器状态"""
        self.vertices = [self.start]
        self.edges = []
        self.parents = {0: None}
        self.planning_time = 0
        self.iterations = 0
        self.path = []
        self.path_length = 0
        self.success = False
        self.expansion_history = []

    def random_sample(self):
        """
        随机采样一个点
        有一定概率直接返回目标点（goal biasing）
        """
        if np.random.random() < self.goal_sample_rate:
            return self.goal.copy()

        # 在配置空间内随机采样
        return self.config_space.sample()

    def nearest_neighbor(self, point):
        """
        找到树中距离给定点最近的节点

        参数:
            point: 给定点坐标

        返回:
            nearest_idx: 最近节点的索引
        """
        # 计算所有节点到给定点的距离
        distances = [np.linalg.norm(np.array(v) - point) for v in self.vertices]
        # 返回最小距离对应的索引
        return np.argmin(distances)

    def steer(self, from_node, to_point):
        """
        从from_node朝to_point方向扩展一个step_size距离的新节点

        参数:
            from_node: 起始节点
            to_point: 目标点

        返回:
            new_point: 新节点坐标
        """
        # 计算方向向量
        direction = to_point - from_node
        # 计算距离
        distance = np.linalg.norm(direction)

        # 如果距离小于步长，直接返回目标点
        if distance < self.step_size:
            return to_point

        # 否则，沿方向扩展step_size距离
        normalized_direction = direction / distance
        return from_node + normalized_direction * self.step_size

    def is_collision_free(self, from_point, to_point):
        """
        检查从from_point到to_point的路径是否无碰撞

        参数:
            from_point: 起始点
            to_point: 终点

        返回:
            bool: 是否无碰撞
        """
        return self.config_space.is_collision_free(from_point, to_point)

    def is_goal_reached(self, point):
        """
        检查是否达到目标点

        参数:
            point: 当前点

        返回:
            bool: 是否达到目标
        """
        distance = np.linalg.norm(point - self.goal)
        return distance < self.step_size / 2  # 降低阈值，使连接更紧密

    def extract_path(self, goal_idx):
        """
        从树中提取路径

        参数:
            goal_idx: 目标点在树中的索引

        返回:
            path: 路径点列表 [[x1, y1], [x2, y2], ...]
        """
        path = []
        current = goal_idx

        # 从目标点沿父节点回溯到起点，添加安全检查防止无限循环
        visited = set()  # 记录已访问的节点，防止循环引用

        while current is not None:
            # 防止循环引用导致的无限循环
            if current in visited:
                print(f"警告：检测到路径中的循环引用，在节点 {current}")
                break

            visited.add(current)

            # 确保索引有效
            if current < 0 or current >= len(self.vertices):
                print(f"警告：无效的节点索引 {current}")
                break

            path.append(self.vertices[current])
            current = self.parents.get(current, None)

        # 路径是从目标点到起点的，需要反转
        return path[::-1]

    def calculate_path_length(self, path):
        """
        计算路径长度

        参数:
            path: 路径点列表

        返回:
            length: 路径长度
        """
        length = 0
        for i in range(len(path) - 1):
            length += np.linalg.norm(path[i + 1] - path[i])
        return length

    def plan(self):
        """
        执行RRT规划算法

        返回:
            success: 是否成功找到路径
            path: 找到的路径 (如果成功)
            vertices: 树的所有节点
            edges: 树的所有边
            planning_time: 规划耗时
        """
        # 重置规划器状态
        self.reset()

        # 记录开始时间
        start_time = time.time()

        for i in range(self.max_iter):
            self.iterations = i + 1

            # 1. 随机采样一个点
            rand_point = self.random_sample()

            # 2. 找到树中最近的节点
            nearest_idx = self.nearest_neighbor(rand_point)
            nearest_point = self.vertices[nearest_idx]

            # 3. 朝随机点方向扩展一步
            new_point = self.steer(nearest_point, rand_point)

            # 4. 检查是否无碰撞
            if not self.is_collision_free(nearest_point, new_point):
                continue

            # 5. 将新节点添加到树中
            self.vertices.append(new_point)
            new_idx = len(self.vertices) - 1
            self.edges.append((nearest_idx, new_idx))
            self.parents[new_idx] = nearest_idx

            # 记录扩展历史，用于可视化
            self.expansion_history.append((nearest_idx, new_idx))

            # 6. 检查是否达到目标
            if self.is_goal_reached(new_point):
                # 提取路径
                self.path = self.extract_path(new_idx)
                self.path_length = self.calculate_path_length(self.path)
                self.success = True
                break

        # 记录规划耗时
        self.planning_time = time.time() - start_time

        return {
            'success': self.success,
            'path': self.path,
            'vertices': self.vertices,
            'edges': self.edges,
            'planning_time': self.planning_time,
            'iterations': self.iterations,
            'expansion_history': self.expansion_history
        }

    def get_name(self):
        """返回算法名称"""
        return "基础RRT算法"

    def get_details(self):
        """返回算法详细信息"""
        return {
            "name": self.get_name(),
            "start": self.start.tolist() if hasattr(self.start, 'tolist') else self.start,
            "goal": self.goal.tolist() if hasattr(self.goal, 'tolist') else self.goal,
            "step_size": self.step_size,
            "goal_sample_rate": self.goal_sample_rate,
            "max_iter": self.max_iter,
            "success": self.success,
            "path_length": self.path_length,
            "planning_time": self.planning_time,
            "iterations": self.iterations,
            "nodes": len(self.vertices)
        }