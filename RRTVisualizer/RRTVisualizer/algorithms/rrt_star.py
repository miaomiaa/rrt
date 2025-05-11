"""
RRT* (RRT Star) 算法实现

RRT*是RRT的改进版本，通过重布线和重组树结构，能够找到接近最优的路径。
该实现包含了错误处理机制，解决了潜在的KeyError问题。
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

        # 计算每个节点到point的距离
        distances = []
        for i, vertex in enumerate(self.vertices):
            distance = np.linalg.norm(vertex - point)
            if distance < radius:
                distances.append((distance, i))

        # 按距离排序
        distances.sort()

        # 只保留最近的max_near_nodes个节点
        for dist, idx in distances[:max_near_nodes]:
            near_indices.append(idx)

        return near_indices

    def new_cost(self, from_idx, to_point):
        """
        计算从起点经过from_idx节点到to_point的总代价
        修复版本，处理KeyError问题

        参数:
            from_idx: 中间节点的索引
            to_point: 目标点坐标

        返回:
            cost: 总代价
        """
        # 如果from_idx不在costs字典中，初始化它
        if from_idx not in self.costs:
            # 尝试计算从起点到该节点的成本
            if from_idx != 0 and from_idx in self.parents:
                parent_idx = self.parents[from_idx]
                if parent_idx in self.costs:
                    parent_cost = self.costs[parent_idx]
                    edge_cost = np.linalg.norm(self.vertices[parent_idx] - self.vertices[from_idx])
                    self.costs[from_idx] = parent_cost + edge_cost
                else:
                    # 如果父节点成本也未知，假设是无穷大，这样的路径就不会被选择
                    self.costs[from_idx] = float('inf')
            else:
                # 如果是起点或无法确定成本，设置为适当的值
                self.costs[from_idx] = 0.0 if from_idx == 0 else float('inf')

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

            # 确保初始化新节点的成本
            if new_idx not in self.costs:
                self.costs[new_idx] = float('inf')  # 初始设置为无穷大

            # 6. 找到新节点附近的节点
            near_indices = self.near_vertices(new_point, search_radius)

            # 7. 选择最优父节点（能够最小化从起点到新节点的代价）
            min_cost = float('inf')
            min_idx = None

            for near_idx in near_indices:
                # 检查从near_idx到new_point是否无碰撞
                if not self.is_collision_free(self.vertices[near_idx], new_point):
                    continue

                try:
                    # 计算经过近邻节点到新节点的代价
                    cost = self.new_cost(near_idx, new_point)

                    if cost < min_cost:
                        min_cost = cost
                        min_idx = near_idx
                except Exception as e:
                    print(f"计算代价时出错: {str(e)}")
                    continue

            # 如果没有找到有效的父节点，使用最近的节点作为父节点
            if min_idx is None:
                min_idx = nearest_idx
                try:
                    min_cost = self.new_cost(nearest_idx, new_point)
                except Exception as e:
                    print(f"计算最近节点代价时出错: {str(e)}")
                    # 使用启发式估计替代
                    min_cost = self.costs.get(nearest_idx, 0.0) + np.linalg.norm(nearest_point - new_point)

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

                # 每隔200次迭代周期性打印信息
                if i % 200 == 0:
                    print(f"迭代 {i}, 当前路径长度: {self.path_length:.2f}")

                # 不退出，继续优化 - 注释掉break允许算法继续寻找更优解
                # break

        # 记录规划耗时
        self.planning_time = time.time() - start_time

        # 打印最终的统计信息
        print(f"RRT*规划完成:")
        print(f"  总迭代次数: {self.iterations}")
        print(f"  节点数量: {len(self.vertices)}")
        print(f"  找到路径: {self.success}")
        print(f"  路径长度: {self.path_length if self.success else 'N/A'}")
        print(f"  规划时间: {self.planning_time:.3f}秒")

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
        修复版本，确保costs字典中包含所有必要的键

        参数:
            new_idx: 新节点的索引
            near_indices: 近邻节点的索引列表
        """
        new_point = self.vertices[new_idx]

        for near_idx in near_indices:
            # 跳过自身
            if near_idx == new_idx:
                continue

            # 确保costs字典中包含near_idx
            if near_idx not in self.costs:
                # 如果没有cost，计算一个初始成本
                parent = self.parents.get(near_idx)
                if parent is not None and parent in self.costs:
                    self.costs[near_idx] = self.costs[parent] + np.linalg.norm(
                        self.vertices[parent] - self.vertices[near_idx]
                    )
                else:
                    # 无法确定路径成本，设置为无穷大
                    self.costs[near_idx] = float('inf')

            # 检查从new_idx到near_idx是否无碰撞
            if not self.is_collision_free(new_point, self.vertices[near_idx]):
                continue

            # 计算经过新节点到近邻节点的代价
            if new_idx not in self.costs:
                # 确保新节点的成本已经计算
                parent = self.parents.get(new_idx)
                if parent is not None and parent in self.costs:
                    self.costs[new_idx] = self.costs[parent] + np.linalg.norm(
                        self.vertices[parent] - self.vertices[new_idx]
                    )
                else:
                    # 无法确定路径成本，设置为无穷大
                    self.costs[new_idx] = float('inf')

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