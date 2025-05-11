import numpy as np
import time
from .base_rrt import BaseRRT


class RRTConnect(BaseRRT):
    """RRT-Connect算法实现类"""

    def __init__(self, start, goal, config_space, step_size=0.5, max_iter=1000):
        """
        初始化RRT-Connect规划器

        参数:
            start: 起始点坐标 [x, y]
            goal: 目标点坐标 [x, y]
            config_space: 配置空间对象
            step_size: 扩展步长
            max_iter: 最大迭代次数
        """
        super().__init__(start, goal, config_space, step_size, 0.0, max_iter)  # 不使用goal biasing

        # 起点树
        self.start_tree = {
            'vertices': [self.start],
            'parents': {0: None}
        }

        # 终点树
        self.goal_tree = {
            'vertices': [self.goal],
            'parents': {0: None}
        }

        # 连接点信息
        self.connection = {
            'found': False,
            'start_idx': None,
            'goal_idx': None
        }

    def reset(self):
        """重置规划器状态"""
        super().reset()

        # 重置起点树
        self.start_tree = {
            'vertices': [self.start],
            'parents': {0: None}
        }

        # 重置终点树
        self.goal_tree = {
            'vertices': [self.goal],
            'parents': {0: None}
        }

        # 重置连接信息
        self.connection = {
            'found': False,
            'start_idx': None,
            'goal_idx': None
        }

    def nearest_neighbor_in_tree(self, point, tree):
        """
        找到指定树中距离给定点最近的节点

        参数:
            point: 给定点坐标
            tree: 树数据结构

        返回:
            nearest_idx: 最近节点的索引
        """
        # 计算所有节点到给定点的距离
        distances = [np.linalg.norm(np.array(v) - point) for v in tree['vertices']]
        # 返回最小距离对应的索引
        return np.argmin(distances)

    def extend(self, tree, target):
        """
        将树朝目标点方向扩展一步

        参数:
            tree: 要扩展的树
            target: 目标点坐标

        返回:
            status: 扩展状态 ('reached', 'advanced', 'trapped')
            new_idx: 新节点的索引（如果成功）
        """
        # 找到树中最近的节点
        nearest_idx = self.nearest_neighbor_in_tree(target, tree)
        nearest_point = tree['vertices'][nearest_idx]

        # 朝目标点方向扩展一步
        new_point = self.steer(nearest_point, target)

        # 检查是否无碰撞
        if not self.is_collision_free(nearest_point, new_point):
            return 'trapped', None

        # 将新节点添加到树中
        tree['vertices'].append(new_point)
        new_idx = len(tree['vertices']) - 1
        tree['parents'][new_idx] = nearest_idx

        # 记录扩展历史
        self.expansion_history.append((nearest_idx, new_idx))

        # 检查是否到达目标点
        if np.linalg.norm(new_point - target) < self.step_size:
            return 'reached', new_idx
        else:
            return 'advanced', new_idx

    def connect(self, tree, target):
        """
        将树持续朝目标点方向扩展，直到到达目标点或被阻挡

        参数:
            tree: 要扩展的树
            target: 目标点坐标

        返回:
            status: 扩展状态 ('reached', 'trapped')
            last_idx: 最后扩展节点的索引（如果成功）
        """
        # 第一次扩展
        status, new_idx = self.extend(tree, target)

        # 如果第一次扩展被阻挡，则返回trapped
        if status == 'trapped':
            return 'trapped', None

        # 持续扩展，直到到达目标点或被阻挡
        while status != 'reached':
            status, newer_idx = self.extend(tree, target)
            new_idx = newer_idx if newer_idx is not None else new_idx

            if status == 'trapped':
                return 'trapped', new_idx

        # 成功到达目标点
        return 'reached', new_idx

    def swap_trees(self):
        """交换起点树和终点树"""
        self.start_tree, self.goal_tree = self.goal_tree, self.start_tree

    def extract_path_from_trees(self):
        """
        从两棵树中提取完整路径

        返回:
            path: 路径点列表
        """
        # 从起点树中提取路径（从起点到连接点）
        start_path = []
        current = self.connection['start_idx']

        while current is not None:
            start_path.append(self.start_tree['vertices'][current])
            current = self.start_tree['parents'][current]

        # 路径是从连接点到起点的，需要反转
        start_path = start_path[::-1]

        # 从终点树中提取路径（从连接点到终点）
        goal_path = []
        current = self.connection['goal_idx']

        while current is not None:
            goal_path.append(self.goal_tree['vertices'][current])
            current = self.goal_tree['parents'][current]

        # 合并路径
        return start_path + goal_path

    def plan(self):
        """
        执行RRT-Connect规划算法

        返回:
            success: 是否成功找到路径
            path: 找到的路径 (如果成功)
            vertices: 两棵树的所有节点
            edges: 两棵树的所有边
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

            # 2. 将起点树向随机点扩展一步
            status_a, new_a_idx = self.extend(self.start_tree, rand_point)

            # 如果成功扩展，则尝试将终点树连接到新节点
            if status_a != 'trapped' and new_a_idx is not None:
                new_a_point = self.start_tree['vertices'][new_a_idx]
                status_b, new_b_idx = self.connect(self.goal_tree, new_a_point)

                # 如果成功连接，则找到路径
                if status_b == 'reached':
                    self.connection['found'] = True
                    self.connection['start_idx'] = new_a_idx
                    self.connection['goal_idx'] = new_b_idx
                    break

            # 交换树，下次从终点树开始扩展
            self.swap_trees()

        # 构建完整的顶点和边列表，用于可视化
        all_vertices = self.start_tree['vertices'] + self.goal_tree['vertices']
        all_edges = []

        # 起点树的边
        for child, parent in self.start_tree['parents'].items():
            if parent is not None:
                all_edges.append((parent, child))

        # 终点树的边，需要偏移索引
        offset = len(self.start_tree['vertices'])
        for child, parent in self.goal_tree['parents'].items():
            if parent is not None:
                all_edges.append((parent + offset, child + offset))

        # 如果成功找到路径，则添加连接两棵树的边
        if self.connection['found']:
            all_edges.append((self.connection['start_idx'],
                              self.connection['goal_idx'] + offset))

            # 提取路径
            self.path = self.extract_path_from_trees()
            self.path_length = self.calculate_path_length(self.path)
            self.success = True

        # 记录规划耗时
        self.planning_time = time.time() - start_time

        return {
            'success': self.success,
            'path': self.path,
            'vertices': all_vertices,
            'edges': all_edges,
            'planning_time': self.planning_time,
            'iterations': self.iterations,
            'expansion_history': self.expansion_history
        }

    def get_name(self):
        """返回算法名称"""
        return "RRT-Connect 算法"

    def get_details(self):
        """返回算法详细信息"""
        details = super().get_details()
        details["name"] = self.get_name()
        if self.success:
            details["start_tree_size"] = len(self.start_tree['vertices'])
            details["goal_tree_size"] = len(self.goal_tree['vertices'])

        return details