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

    def reset(self):
        """重置规划器状态"""
        super().reset()
        self.best_path_length = float('inf')
        self.ellipse_transform = None
        self.initial_solution_found = False

    def compute_ellipse_transform(self):
        """
        计算椭圆采样的变换矩阵
        椭圆的焦点是起点和终点，长轴长度是当前最佳路径长度
        """
        # 计算起点到终点的距离
        c_best = np.linalg.norm(self.goal - self.start)

        # 如果起点和终点重合，则不需要椭圆变换
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

        # 椭圆的短半轴长度
        r2 = np.sqrt(self.best_path_length ** 2 - c_best ** 2) / 2.0

        # 构建变换矩阵
        C = np.vstack([a1, a2]).T
        L = np.diag([r1, r2])

        # 返回变换矩阵、中心点和半轴长度
        return {'C': C, 'L': L, 'center': center}

    def informed_sample(self):
        """
        在找到初始解后，使用椭圆采样
        否则使用普通采样
        """
        # 如果没有找到初始解或者采样目标点，则使用普通采样
        if not self.initial_solution_found or np.random.random() < self.goal_sample_rate:
            return super().random_sample()

        # 计算椭圆变换（如果尚未计算）
        if self.ellipse_transform is None:
            self.ellipse_transform = self.compute_ellipse_transform()

            # 如果变换计算失败，则使用普通采样
            if self.ellipse_transform is None:
                return super().random_sample()

        # 在单位球内均匀采样
        while True:
            # 在单位圆内均匀采样
            x_ball = np.random.uniform(-1, 1, 2)
            if np.linalg.norm(x_ball) <= 1:
                break

        # 应用椭圆变换
        x_ellipse = self.ellipse_transform['C'] @ (self.ellipse_transform['L'] @ x_ball)
        sample = self.ellipse_transform['center'] + x_ellipse

        # 确保样本在配置空间内
        if not self.config_space.is_in_bounds(sample):
            return super().random_sample()

        return sample

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
        import time
        start_time = time.time()

        # 动态调整搜索半径（可选）
        # 随着节点数量的增加，搜索半径可以适当减小
        search_radius = self.search_radius

        for i in range(self.max_iter):
            self.iterations = i + 1

            # 1. 采样一个点（可能是有信息的采样）
            if self.initial_solution_found:
                rand_point = self.informed_sample()
            else:
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

                # 更新最佳路径长度和椭圆变换
                if self.path_length < self.best_path_length:
                    self.best_path_length = self.path_length
                    self.ellipse_transform = self.compute_ellipse_transform()

                # 标记为找到初始解
                self.initial_solution_found = True
                self.success = True

                # 不要退出循环，继续优化路径

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
        return "Informed RRT* 算法"

    def get_details(self):
        """返回算法详细信息"""
        details = super().get_details()
        details["name"] = self.get_name()
        details["best_path_length"] = self.best_path_length
        details["initial_solution_found"] = self.initial_solution_found

        return details