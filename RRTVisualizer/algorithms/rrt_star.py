"""
RRT* (RRT Star) 算法实现

RRT*是RRT的改进版本，通过重布线和重组树结构，能够找到接近最优的路径。
"""
"""
RRT* (RRT Star) 算法实现

RRT*是RRT的改进版本，通过重布线和重组树结构，能够找到接近最优的路径。
"""

import numpy as np
import time
from .base_rrt import BaseRRT


class RRTStar(BaseRRT):
    """RRT*算法实现类"""

    def __init__(self, start, goal, config_space, step_size=0.5, goal_sample_rate=0.05,
                 max_iter=1000, search_radius=1.0):
        """
        初始化RRT*规划器

        参数:
            start: 起始点坐标 [x, y]
            goal: 目标点坐标 [x, y]
            config_space: 配置空间对象
            step_size: 扩展步长
            goal_sample_rate: 采样目标点的概率
            max_iter: 最大迭代次数
            search_radius: 近邻搜索半径
        """
        super().__init__(start, goal, config_space, step_size, goal_sample_rate, max_iter)
        self.search_radius = search_radius

        # 存储从起点到每个节点的代价
        self.costs = {0: 0.0}  # 起点的代价为0

    def reset(self):
        """重置规划器状态"""
        super().reset()
        self.costs = {0: 0.0}

    def near_vertices(self, point, radius):
        """
        找到树中在给定半径内的所有节点

        参数:
            point: 给定点坐标
            radius: 搜索半径

        返回:
            near_indices: 邻近节点的索引列表
        """
        near_indices = []

        # 优化：限制近邻节点的最大数量，防止在高密度区域产生过多近邻
        max_near_nodes = 50  # 设置一个合理的上限

        for i, vertex in enumerate(self.vertices):
            distance = np.linalg.norm(vertex - point)
            if distance < radius:
                near_indices.append(i)

                # 如果近邻节点数量达到上限，排序并只保留最近的节点
                if len(near_indices) > max_near_nodes:
                    # 计算所有近邻节点到点的距离
                    distances = [np.linalg.norm(self.vertices[idx] - point) for idx in near_indices]
                    # 根据距离排序
                    sorted_indices = [idx for _, idx in sorted(zip(distances, near_indices))]
                    # 只保留最近的max_near_nodes个节点
                    near_indices = sorted_indices[:max_near_nodes]

        return near_indices

    def new_cost(self, from_idx, to_point):
        """
        计算从起点经过from_idx节点到to_point的总代价

        参数:
            from_idx: 中间节点的索引
            to_point: 目标点坐标

        返回:
            cost: 总代价
        """
        # 从起点到中间节点的代价
        from_cost = self.costs[from_idx]
        # 中间节点到目标点的代价（欧式距离）
        to_cost = np.linalg.norm(self.vertices[from_idx] - to_point)

        return from_cost + to_cost

    def plan(self):
        """
        执行RRT*规划算法

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
        import time
        start_time = time.time()

        # 动态调整搜索半径（可选）
        # 随着节点数量的增加，搜索半径可以适当减小
        search_radius = self.search_radius

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

            # 6. 找到新节点附近的节点
            near_indices = self.near_vertices(new_point, search_radius)

            # 7. 选择最优父节点（能够最小化从起点到新节点的代价）
            min_cost = float('inf')
            min_idx = None

            for near_idx in near_indices:
                # 检查从near_idx到new_point是否无碰撞
                if not self.is_collision_free(self.vertices[near_idx], new_point):
                    continue

                # 计算经过近邻节点到新节点的代价
                cost = self.new_cost(near_idx, new_point)

                if cost < min_cost:
                    min_cost = cost
                    min_idx = near_idx

            # 如果没有找到有效的父节点，使用最近的节点作为父节点
            if min_idx is None:
                min_idx = nearest_idx
                min_cost = self.new_cost(nearest_idx, new_point)

            # 更新父节点和代价
            self.parents[new_idx] = min_idx
            self.edges.append((min_idx, new_idx))
            self.costs[new_idx] = min_cost

            # 记录扩展历史，用于可视化
            self.expansion_history.append((min_idx, new_idx))

            # 8. 重布线：检查是否可以通过新节点改进近邻节点的路径
            self.rewire(new_idx, near_indices)

            # 9. 检查是否达到目标
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

    def rewire(self, new_idx, near_indices):
        """
        重布线操作：检查是否可以通过新节点来改进近邻节点的路径

        参数:
            new_idx: 新节点的索引
            near_indices: 近邻节点的索引列表
        """
        new_point = self.vertices[new_idx]

        for near_idx in near_indices:
            # 跳过自身
            if near_idx == new_idx:
                continue

            # 检查从new_idx到near_idx是否无碰撞
            if not self.is_collision_free(new_point, self.vertices[near_idx]):
                continue

            # 计算经过新节点到近邻节点的代价
            cost = self.costs[new_idx] + np.linalg.norm(new_point - self.vertices[near_idx])

            # 如果代价更低，则更新父节点和代价
            if cost < self.costs[near_idx]:
                # 更新父节点
                old_parent = self.parents[near_idx]
                self.parents[near_idx] = new_idx

                # 更新边
                self.edges = [(p, c) for (p, c) in self.edges if c != near_idx]  # 删除旧边
                self.edges.append((new_idx, near_idx))  # 添加新边

                # 更新代价
                self.costs[near_idx] = cost

                # 记录重布线历史，用于可视化
                self.expansion_history.append((new_idx, near_idx))

    def get_name(self):
        """返回算法名称"""
        return "RRT* 算法"

    def get_details(self):
        """返回算法详细信息"""
        details = super().get_details()
        details["name"] = self.get_name()
        details["search_radius"] = self.search_radius

        return details