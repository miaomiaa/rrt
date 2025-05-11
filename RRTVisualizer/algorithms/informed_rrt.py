"""
Informed RRT* 算法实现

Informed RRT*是RRT*的改进版本，在找到初始解后，使用椭圆采样
来限制搜索空间，加速收敛到最优解。
"""

import numpy as np
import time
from .rrt_star import RRTStar


class InformedRRT(RRTStar):
    """Informed RRT*算法实现类"""

    def __init__(self, start, goal, config_space, step_size=0.5, goal_sample_rate=0.05,
                 max_iter=1000, search_radius=1.0):
        """
        初始化Informed RRT*规划器

        参数:
            start: 起始点坐标 [x, y]
            goal: 目标点坐标 [x, y]
            config_space: 配置空间对象
            step_size: 扩展步长
            goal_sample_rate: 采样目标点的概率
            max_iter: 最大迭代次数
            search_radius: 近邻搜索半径
        """
        super().__init__(start, goal, config_space, step_size, goal_sample_rate, max_iter, search_radius)

        # 当前最佳路径长度，用于构建采样椭圆
        self.best_path_length = float('inf')

        # 椭圆变换矩阵
        self.ellipse_transform = None

        # 初始解找到的标志
        self.initial_solution_found = False

        # 调试数据
        self.ellipse_samples_count = 0
        self.regular_samples_count = 0

    def reset(self):
        """重置规划器状态"""
        super().reset()
        self.best_path_length = float('inf')
        self.ellipse_transform = None
        self.initial_solution_found = False
        self.ellipse_samples_count = 0
        self.regular_samples_count = 0

    def compute_ellipse_transform(self):
        """
        计算椭圆采样的变换矩阵
        椭圆的焦点是起点和终点，长轴长度是当前最佳路径长度
        """
        # 计算起点到终点的距离
        c_best = np.linalg.norm(self.goal - self.start)

        # 如果起点和终点重合或距离很小，则不需要椭圆变换
        if c_best < 1e-6:
            return None

        # 椭圆的中心
        center = (self.start + self.goal) / 2.0

        # 计算从世界坐标系到椭圆坐标系的旋转矩阵
        a1 = (self.goal - self.start) / c_best

        # 构建正交基
        a2 = np.array([-a1[1], a1[0]])

        # 椭圆的长半轴长度
        r1 = self.best_path_length / 2.0

        # 椭圆的短半轴长度 - 确保计算有效
        h_sq = max(0, self.best_path_length**2 - c_best**2) / 4.0  # 避免负数
        r2 = np.sqrt(h_sq)

        # 构建变换矩阵
        C = np.vstack([a1, a2]).T
        L = np.diag([r1, r2])

        # 返回变换矩阵、中心点和半轴长度
        return {'C': C, 'L': L, 'center': center, 'r1': r1, 'r2': r2}

    def informed_sample(self):
        """
        在找到初始解后，使用椭圆采样
        否则使用普通采样
        """
        # 如果没有找到初始解或者按概率采样目标点，则使用普通采样
        if not self.initial_solution_found:
            self.regular_samples_count += 1
            return super().random_sample()

        # 有小概率选择目标点
        if np.random.random() < self.goal_sample_rate:
            return self.goal.copy()

        # 计算椭圆变换（如果尚未计算或需要更新）
        if self.ellipse_transform is None:
            self.ellipse_transform = self.compute_ellipse_transform()

            # 如果变换计算失败，则使用普通采样
            if self.ellipse_transform is None:
                self.regular_samples_count += 1
                return super().random_sample()

        # 在单位球内均匀采样
        max_attempts = 100
        for _ in range(max_attempts):
            # 在单位圆内均匀采样
            while True:
                x_ball = np.random.uniform(-1, 1, 2)
                if np.linalg.norm(x_ball) <= 1:
                    break

            # 应用椭圆变换
            try:
                x_ellipse = self.ellipse_transform['C'] @ (self.ellipse_transform['L'] @ x_ball)
                sample = self.ellipse_transform['center'] + x_ellipse
            except:
                # 如果变换出错，使用普通采样
                self.regular_samples_count += 1
                return super().random_sample()

            # 确保样本在配置空间内
            if self.config_space.is_in_bounds(sample):
                self.ellipse_samples_count += 1
                return sample

        # 如果多次尝试都失败，则使用普通采样
        self.regular_samples_count += 1
        return super().random_sample()

    def new_cost(self, from_idx, to_point):
        """
        计算从起点经过from_idx节点到to_point的总代价
        修复KeyError问题

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
                # 如果是起点或无法确定成本，设置为无穷大
                self.costs[from_idx] = 0.0 if from_idx == 0 else float('inf')

        # 从起点到中间节点的代价
        from_cost = self.costs[from_idx]
        # 中间节点到目标点的代价（欧式距离）
        to_cost = np.linalg.norm(self.vertices[from_idx] - to_point)

        return from_cost + to_cost

    def plan(self):
        """
        执行Informed RRT*规划算法

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

            # 1. 采样一个点（可能是有信息的采样）
            rand_point = self.informed_sample()

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

                # 更新最佳路径长度
                if self.path_length < self.best_path_length:
                    self.best_path_length = self.path_length
                    # 每次找到更好的路径时重新计算椭圆变换
                    self.ellipse_transform = self.compute_ellipse_transform()
                    # 打印最佳路径长度，帮助调试
                    print(f"更新最佳路径，长度: {self.best_path_length:.2f}")

                # 标记为找到初始解
                if not self.initial_solution_found:
                    self.initial_solution_found = True
                    print(f"找到初始解，长度: {self.path_length:.2f}")

                self.success = True

                # 不要退出循环，继续优化路径

            # 动态调整搜索半径（可选）- 随着节点数增加，减小搜索半径
            if self.initial_solution_found and i % 100 == 0 and i > 0:
                # 计算节点密度
                node_density = len(self.vertices) / (self.config_space.bounds['x_max'] * self.config_space.bounds['y_max'])
                # 根据节点密度调整搜索半径
                adjusted_radius = self.search_radius / np.sqrt(node_density * 1000)
                # 限制最小和最大值
                search_radius = max(min(adjusted_radius, self.search_radius), self.search_radius * 0.3)

        # 记录规划耗时
        self.planning_time = time.time() - start_time

        # 打印算法统计信息
        print(f"InformedRRT*规划完成:")
        print(f"  总迭代次数: {self.iterations}")
        print(f"  节点数量: {len(self.vertices)}")
        print(f"  找到路径: {self.success}")
        print(f"  规划时间: {self.planning_time:.3f}秒")
        print(f"  路径长度: {self.path_length if self.success else 'N/A'}")
        print(f"  椭圆采样次数: {self.ellipse_samples_count}")
        print(f"  普通采样次数: {self.regular_samples_count}")
        if self.success:
            self.simplify_tree_for_visualization()

        if self.ellipse_transform:
            print(f"  椭圆信息: 长半轴={self.ellipse_transform['r1']:.2f}, 短半轴={self.ellipse_transform['r2']:.2f}")

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
        修复版本，确保costs字典中包含所有必要的键并保持数据一致性

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
                    print(f"警告: 重布线中节点 {near_idx} 的父节点 {parent} 没有成本值")

            # 检查从new_idx到near_idx是否无碰撞
            if not self.is_collision_free(new_point, self.vertices[near_idx]):
                continue

            try:
                # 确保new_idx在costs字典中
                if new_idx not in self.costs:
                    parent = self.parents.get(new_idx)
                    if parent is not None and parent in self.costs:
                        self.costs[new_idx] = self.costs[parent] + np.linalg.norm(
                            self.vertices[parent] - self.vertices[new_idx]
                        )
                    else:
                        self.costs[new_idx] = float('inf')
                        print(f"警告: 重布线中节点 {new_idx} 的父节点 {parent} 没有成本值")

                # 计算经过新节点到近邻节点的代价
                cost = self.costs[new_idx] + np.linalg.norm(new_point - self.vertices[near_idx])

                # 如果代价更低，则更新父节点和代价
                if cost < self.costs[near_idx]:
                    # 保存旧状态以便回滚
                    old_parent = self.parents[near_idx]
                    old_cost = self.costs[near_idx]

                    # 原子化更新操作
                    # 1. 更新父节点引用
                    self.parents[near_idx] = new_idx

                    # 2. 更新边集合 - 安全更新
                    new_edges = [(p, c) for (p, c) in self.edges if c != near_idx]
                    new_edges.append((new_idx, near_idx))
                    self.edges = new_edges

                    # 3. 更新代价
                    self.costs[near_idx] = cost

                    # 4. 记录重布线历史
                    self.expansion_history.append((new_idx, near_idx))

                    # 验证更新是否成功
                    if near_idx not in self.parents or self.parents[near_idx] != new_idx:
                        print(f"错误: 更新父节点失败 - 节点 {near_idx}")
                        # 回滚更改
                        self.parents[near_idx] = old_parent
                        self.costs[near_idx] = old_cost
                        self.edges = [(p, c) for (p, c) in self.edges if c != near_idx]
                        if old_parent is not None:
                            self.edges.append((old_parent, near_idx))

            except Exception as e:
                print(f"重布线过程出现异常: {e}")
                # 任何异常情况下，确保数据一致性
                if 'old_parent' in locals() and 'old_cost' in locals():
                    self.parents[near_idx] = old_parent
                    self.costs[near_idx] = old_cost
                    self.edges = [(p, c) for (p, c) in self.edges if c != near_idx]
                    if old_parent is not None:
                        self.edges.append((old_parent, near_idx))

    def get_name(self):
        """返回算法名称"""
        return "Informed RRT* 算法"

    def get_details(self):
        """返回算法详细信息"""
        details = super().get_details()
        details["name"] = self.get_name()
        details["best_path_length"] = self.best_path_length
        details["initial_solution_found"] = self.initial_solution_found
        details["ellipse_samples_count"] = self.ellipse_samples_count
        details["regular_samples_count"] = self.regular_samples_count

        if self.ellipse_transform:
            details["ellipse_long_axis"] = float(self.ellipse_transform['r1']) * 2
            details["ellipse_short_axis"] = float(self.ellipse_transform['r2']) * 2

        return details