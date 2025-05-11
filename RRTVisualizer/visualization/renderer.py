"""
渲染引擎，用于RRT算法可视化
"""

import numpy as np
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter
from PyQt5.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsSimpleTextItem,
    QGraphicsItemGroup
)

from .graphics_items import (
    StartPoint, GoalPoint, TreeNode, TreeEdge, PathSegment, ObstacleItem
)


class Renderer(QGraphicsView):
    """RRT算法可视化渲染器"""

    def __init__(self, parent=None):
        """
        初始化渲染器

        参数:
            parent: 父窗口
        """
        super().__init__(parent)

        # 创建场景
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # 设置视图属性
        self.setRenderHint(QPainter.Antialiasing)  # 修复：使用QPainter的抗锯齿设置
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # 跟踪鼠标
        self.setMouseTracking(True)

        # 缓存图形项，方便更新
        self._start_point = None
        self._goal_point = None
        self._nodes = []
        self._edges = []
        self._path_segments = []
        self._obstacle_items = []
        self._grid_lines = []

        # 坐标显示
        self._coord_text = QGraphicsSimpleTextItem()
        self._coord_text.setPos(10, 10)
        self._coord_text.setZValue(100)
        self.scene.addItem(self._coord_text)

        # 网格开关
        self._show_grid = True
        self._grid_size = 50  # 网格大小

        # 配置空间边界
        self._bounds = {
            'x_min': 0,
            'x_max': 800,
            'y_min': 0,
            'y_max': 600
        }

        # 初始化场景
        self._init_scene()

    def _init_scene(self):
        """初始化场景"""
        # 设置场景范围
        margin = 100  # 边距
        self.scene.setSceneRect(
            QRectF(
                self._bounds['x_min'] - margin,
                self._bounds['y_min'] - margin,
                self._bounds['x_max'] - self._bounds['x_min'] + 2 * margin,
                self._bounds['y_max'] - self._bounds['y_min'] + 2 * margin
            )
        )

        # 设置背景颜色
        self.setBackgroundBrush(QBrush(QColor(248, 248, 252)))  # 浅灰蓝色背景

        # 添加边界矩形
        border = QGraphicsRectItem(
            self._bounds['x_min'],
            self._bounds['y_min'],
            self._bounds['x_max'] - self._bounds['x_min'],
            self._bounds['y_max'] - self._bounds['y_min']
        )
        # 使用半透明的灰色边框，更加优雅
        border_pen = QPen(QColor(80, 80, 80, 200), 2)
        border_pen.setStyle(Qt.SolidLine)
        border.setPen(border_pen)
        border.setBrush(QBrush(QColor(255, 255, 255)))  # 白色填充
        self.scene.addItem(border)

        # 绘制网格
        self._draw_grid()

    def set_bounds(self, bounds):
        """
        设置配置空间边界

        参数:
            bounds: 边界字典 {'x_min', 'x_max', 'y_min', 'y_max'}
        """
        self._bounds = bounds
        self._init_scene()

    def _draw_grid(self):
        """绘制网格"""
        # 清除旧网格
        for line in self._grid_lines:
            self.scene.removeItem(line)
        self._grid_lines = []

        if not self._show_grid:
            return

        # 使用更浅的颜色和不同的线型，使网格更加优雅
        minor_grid_color = QColor(220, 220, 225, 100)  # 半透明浅灰色
        major_grid_color = QColor(180, 180, 190, 150)  # 较深的网格线用于主网格线

        # 绘制水平网格线
        for y in range(
                int(self._bounds['y_min']),
                int(self._bounds['y_max']) + 1,
                self._grid_size
        ):
            line = QGraphicsRectItem(
                self._bounds['x_min'],
                y,
                self._bounds['x_max'] - self._bounds['x_min'],
                1
            )

            # 主网格线（100的倍数）使用更显眼的样式
            if y % (self._grid_size * 2) == 0:
                pen = QPen(major_grid_color, 1)
                pen.setStyle(Qt.DashLine)
            else:
                pen = QPen(minor_grid_color, 1)
                pen.setStyle(Qt.DotLine)

            line.setPen(pen)
            self.scene.addItem(line)
            self._grid_lines.append(line)

        # 绘制垂直网格线
        for x in range(
                int(self._bounds['x_min']),
                int(self._bounds['x_max']) + 1,
                self._grid_size
        ):
            line = QGraphicsRectItem(
                x,
                self._bounds['y_min'],
                1,
                self._bounds['y_max'] - self._bounds['y_min']
            )

            # 主网格线（100的倍数）使用更显眼的样式
            if x % (self._grid_size * 2) == 0:
                pen = QPen(major_grid_color, 1)
                pen.setStyle(Qt.DashLine)
            else:
                pen = QPen(minor_grid_color, 1)
                pen.setStyle(Qt.DotLine)

            line.setPen(pen)
            self.scene.addItem(line)
            self._grid_lines.append(line)

    def toggle_grid(self):
        """切换网格显示状态"""
        self._show_grid = not self._show_grid
        self._draw_grid()

    def set_grid_size(self, size):
        """
        设置网格大小

        参数:
            size: 网格大小
        """
        self._grid_size = size
        self._draw_grid()

    def clear(self):
        """清除所有图形项"""
        # 移除起点
        if self._start_point:
            self.scene.removeItem(self._start_point)
            self._start_point = None

        # 移除终点
        if self._goal_point:
            self.scene.removeItem(self._goal_point)
            self._goal_point = None

        # 移除树节点
        for node in self._nodes:
            self.scene.removeItem(node)
        self._nodes = []

        # 移除树边
        for edge in self._edges:
            self.scene.removeItem(edge)
        self._edges = []

        # 移除路径段
        for segment in self._path_segments:
            self.scene.removeItem(segment)
        self._path_segments = []

        # 移除障碍物
        for item in self._obstacle_items:
            self.scene.removeItem(item)
        self._obstacle_items = []

        # 重新初始化场景
        self._init_scene()

    def set_start_point(self, x, y):
        """
        设置起点

        参数:
            x, y: 起点坐标
        """
        # 移除旧起点
        if self._start_point:
            self.scene.removeItem(self._start_point)

        # 创建新起点
        self._start_point = StartPoint(x, y)
        self.scene.addItem(self._start_point)

    def set_goal_point(self, x, y):
        """
        设置终点

        参数:
            x, y: 终点坐标
        """
        # 移除旧终点
        if self._goal_point:
            self.scene.removeItem(self._goal_point)

        # 创建新终点
        self._goal_point = GoalPoint(x, y)
        self.scene.addItem(self._goal_point)

    def add_obstacle(self, obstacle):
        """
        添加障碍物

        参数:
            obstacle: 障碍物对象
        """
        # 创建障碍物图形项
        item = ObstacleItem.create_from_obstacle(obstacle)
        self.scene.addItem(item)
        self._obstacle_items.append(item)

    def clear_obstacles(self):
        """清除所有障碍物"""
        for item in self._obstacle_items:
            self.scene.removeItem(item)
        self._obstacle_items = []

    def add_tree_node(self, x, y):
        """
        添加树节点

        参数:
            x, y: 节点坐标

        返回:
            node: 节点图形项
        """
        node = TreeNode(x, y)
        self.scene.addItem(node)
        self._nodes.append(node)
        return node

    def add_tree_edge(self, x1, y1, x2, y2):
        """
        添加树边

        参数:
            x1, y1: 起点坐标
            x2, y2: 终点坐标

        返回:
            edge: 边图形项
        """
        edge = TreeEdge(x1, y1, x2, y2)
        self.scene.addItem(edge)
        self._edges.append(edge)
        return edge

    def add_path_segment(self, x1, y1, x2, y2):
        """
        添加路径段

        参数:
            x1, y1: 起点坐标
            x2, y2: 终点坐标

        返回:
            segment: 路径段图形项
        """
        segment = PathSegment(x1, y1, x2, y2)
        self.scene.addItem(segment)
        self._path_segments.append(segment)
        return segment

    def clear_path(self):
        """清除路径"""
        for segment in self._path_segments:
            self.scene.removeItem(segment)
        self._path_segments = []

    def clear_tree(self):
        """清除树"""
        # 清除树节点
        for node in self._nodes:
            self.scene.removeItem(node)
        self._nodes = []

        # 清除树边
        for edge in self._edges:
            self.scene.removeItem(edge)
        self._edges = []

    def visualize_rrt(self, result):
        """
        可视化RRT算法结果

        参数:
            result: 算法结果字典，包含以下键：
                - vertices: 树节点列表
                - edges: 树边列表
                - path: 路径点列表
        """
        try:
            # 清除旧的树和路径
            self.clear_tree()
            self.clear_path()

            # 如果结果无效，直接返回
            if not result or not isinstance(result, dict):
                print("无效的RRT结果")
                return

            if 'vertices' not in result or 'edges' not in result:
                print("RRT结果缺少必要字段")
                return

            # 优化：如果节点太多，只显示一部分
            max_nodes_to_display = 5000  # 设置一个合理的上限

            vertices = result.get('vertices', [])
            edges = result.get('edges', [])

            # 如果节点过多，进行采样显示
            if len(vertices) > max_nodes_to_display:
                import random
                # 随机选择一部分边来显示
                sample_size = max_nodes_to_display
                sampled_edges = random.sample(edges, min(sample_size, len(edges)))

                # 找出采样边中包含的所有节点
                node_set = set()
                for e in sampled_edges:
                    node_set.add(e[0])
                    node_set.add(e[1])

                # 只显示采样中包含的节点
                for i in node_set:
                    if i < len(vertices):
                        v = vertices[i]
                        self.add_tree_node(v[0], v[1])

                # 显示采样的边
                for e in sampled_edges:
                    if e[0] < len(vertices) and e[1] < len(vertices):
                        v1 = vertices[e[0]]
                        v2 = vertices[e[1]]
                        self.add_tree_edge(v1[0], v1[1], v2[0], v2[1])

                print(
                    f"注意：只显示了 {len(node_set)} 个节点和 {len(sampled_edges)} 条边，总共有 {len(vertices)} 个节点和 {len(edges)} 条边")
            else:
                # 显示所有节点和边
                for v in vertices:
                    self.add_tree_node(v[0], v[1])

                for e in edges:
                    if e[0] < len(vertices) and e[1] < len(vertices):
                        v1 = vertices[e[0]]
                        v2 = vertices[e[1]]
                        self.add_tree_edge(v1[0], v1[1], v2[0], v2[1])

            # 如果找到路径，则可视化
            if result.get('success', False) and 'path' in result and result['path']:
                path = result['path']
                if len(path) > 1:  # 确保路径至少有两个点
                    for i in range(len(path) - 1):
                        self.add_path_segment(path[i][0], path[i][1], path[i + 1][0], path[i + 1][1])

        except Exception as e:
            import traceback
            print(f"可视化RRT结果时出错: {str(e)}")
            print(traceback.format_exc())

    def visualize_expansion(self, from_idx, to_idx, vertices):
        """
        可视化树的扩展过程

        参数:
            from_idx: 父节点索引
            to_idx: 子节点索引
            vertices: 所有节点的坐标列表
        """
        v1 = vertices[from_idx]
        v2 = vertices[to_idx]

        # 添加新节点
        self.add_tree_node(v2[0], v2[1])

        # 添加新边
        self.add_tree_edge(v1[0], v1[1], v2[0], v2[1])

    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件，实现缩放功能

        参数:
            event: 滚轮事件
        """
        factor = 1.2

        if event.angleDelta().y() < 0:
            factor = 1.0 / factor

        self.scale(factor, factor)

    def mouseMoveEvent(self, event):
        """
        处理鼠标移动事件，显示坐标

        参数:
            event: 鼠标事件
        """
        super().mouseMoveEvent(event)

        # 获取鼠标在场景中的位置
        pos = self.mapToScene(event.pos())

        # 更新坐标显示
        self._coord_text.setText(f"X: {pos.x():.1f}, Y: {pos.y():.1f}")

    def fit_view(self):
        """适应视图大小"""
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def save_as_image(self, file_path):
        """
        将场景保存为图片

        参数:
            file_path: 图片保存路径
        """
        from PyQt5.QtGui import QImage, QPainter

        # 创建图片
        image = QImage(
            int(self.scene.sceneRect().width()),
            int(self.scene.sceneRect().height()),
            QImage.Format_ARGB32
        )
        image.fill(Qt.white)

        # 绘制场景到图片
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()

        # 保存图片
        image.save(file_path)
        return True