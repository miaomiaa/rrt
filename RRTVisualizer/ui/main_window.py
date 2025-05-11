"""
主窗口类，整合所有UI组件
"""

import os
import json
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QAction, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtGui import QPainter

from algorithms import BaseRRT, RRTStar, RRTConnect, InformedRRT
from environment import ConfigurationSpace, RectangleObstacle, CircleObstacle, PolygonObstacle
from visualization import Renderer
from .control_panel import ControlPanel
from .result_panel import ResultPanel
from utils import export_to_csv, export_to_image


class MainWindow(QMainWindow):
    """RRT算法可视化主窗口"""

    def __init__(self):
        """初始化主窗口"""
        super().__init__()

        # 设置窗口属性
        self.setWindowTitle("RRT算法可视化工具")
        self.resize(1280, 800)

        # 初始化GUI组件
        self._init_ui()

        # 初始化菜单
        self._init_menu()

        # 初始化状态栏
        self.statusBar().showMessage("就绪")

        # 创建配置空间
        self.config_space = ConfigurationSpace(800, 600)

        # 创建算法对象
        self._init_algorithms()

        # 当前选择的算法
        self.current_algorithm = self.algorithms["BaseRRT"]

        # 规划状态
        self.is_planning = False
        self.expansion_timer = QTimer(self)
        self.expansion_timer.timeout.connect(self._animate_expansion)
        self.expansion_index = 0

        # 连接控制面板信号
        self._connect_signals()

    def _init_ui(self):
        """初始化界面布局"""
        # 创建中心窗口部件
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 创建左侧面板（控制面板）
        self.control_panel = ControlPanel()
        splitter.addWidget(self.control_panel)

        # 创建中间部件（渲染区域）
        self.renderer = Renderer()
        splitter.addWidget(self.renderer)

        # 创建右侧面板（结果面板）
        self.result_panel = ResultPanel()
        splitter.addWidget(self.result_panel)

        # 设置分割器的初始大小
        splitter.setSizes([300, 600, 300])

    def _init_menu(self):
        """初始化菜单栏"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件")

        # 新建
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)

        # 打开
        open_action = QAction("打开...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        # 保存
        save_action = QAction("保存...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # 导出
        export_menu = file_menu.addMenu("导出")

        # 导出为图片
        export_image_action = QAction("导出为图片...", self)
        export_image_action.triggered.connect(self._on_export_image)
        export_menu.addAction(export_image_action)

        # 导出为CSV
        export_csv_action = QAction("导出结果为CSV...", self)
        export_csv_action.triggered.connect(self._on_export_csv)
        export_menu.addAction(export_csv_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = self.menuBar().addMenu("视图")

        # 显示/隐藏网格
        toggle_grid_action = QAction("显示网格", self)
        toggle_grid_action.setCheckable(True)
        toggle_grid_action.setChecked(True)
        toggle_grid_action.triggered.connect(self.renderer.toggle_grid)
        view_menu.addAction(toggle_grid_action)

        # 适应视图
        fit_view_action = QAction("适应视图", self)
        fit_view_action.setShortcut("Ctrl+F")
        fit_view_action.triggered.connect(self.renderer.fit_view)
        view_menu.addAction(fit_view_action)

        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助")

        # 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _init_algorithms(self):
        """初始化算法对象"""
        self.algorithms = {
            "BaseRRT": BaseRRT(
                [0, 0], [0, 0], self.config_space,
                step_size=20, goal_sample_rate=0.05, max_iter=1000
            ),
            "RRTStar": RRTStar(
                [0, 0], [0, 0], self.config_space,
                step_size=20, goal_sample_rate=0.05, max_iter=3000, search_radius=50
            ),
            "RRTConnect": RRTConnect(
                [0, 0], [0, 0], self.config_space,
                step_size=20, max_iter=1500
            ),
            "InformedRRT": InformedRRT(
                [0, 0], [0, 0], self.config_space,
                step_size=20, goal_sample_rate=0.05, max_iter=3000, search_radius=50
            )
        }

    def _connect_signals(self):
        """连接信号槽"""
        # 控制面板信号
        self.control_panel.start_button.clicked.connect(self._on_start)
        self.control_panel.stop_button.clicked.connect(self._on_stop)
        self.control_panel.reset_button.clicked.connect(self._on_reset)
        self.control_panel.algorithm_combo.currentIndexChanged.connect(self._on_algorithm_changed)
        self.control_panel.step_size_spin.valueChanged.connect(self._on_step_size_changed)
        self.control_panel.max_iter_spin.valueChanged.connect(self._on_max_iter_changed)
        self.control_panel.goal_sample_rate_spin.valueChanged.connect(self._on_goal_sample_rate_changed)
        self.control_panel.search_radius_spin.valueChanged.connect(self._on_search_radius_changed)
        self.control_panel.animation_speed_slider.valueChanged.connect(self._on_animation_speed_changed)

        # 障碍物控制
        self.control_panel.add_rectangle_button.clicked.connect(self._on_add_rectangle)
        self.control_panel.add_circle_button.clicked.connect(self._on_add_circle)
        self.control_panel.clear_obstacles_button.clicked.connect(self._on_clear_obstacles)

        # 起终点控制
        self.control_panel.set_start_button.clicked.connect(self._on_set_start)
        self.control_panel.set_goal_button.clicked.connect(self._on_set_goal)

    def _on_new(self):
        """新建文件"""
        reply = QMessageBox.question(
            self, "确认", "是否创建新文件？当前数据将丢失。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._on_reset()

    def _on_open(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # 清除当前数据
                self._on_reset()

                # 加载配置空间
                if 'bounds' in data:
                    self.config_space = ConfigurationSpace(
                        data['bounds']['x_max'],
                        data['bounds']['y_max']
                    )
                    self.renderer.set_bounds(data['bounds'])

                # 加载障碍物
                if 'obstacles' in data:
                    for obs in data['obstacles']:
                        if obs['type'] == 'rectangle':
                            obstacle = RectangleObstacle(
                                obs['x'], obs['y'], obs['width'], obs['height'],
                                obs.get('color', 'black')
                            )
                        elif obs['type'] == 'circle':
                            obstacle = CircleObstacle(
                                obs['center_x'], obs['center_y'], obs['radius'],
                                obs.get('color', 'black')
                            )
                        elif obs['type'] == 'polygon':
                            obstacle = PolygonObstacle(
                                obs['vertices'],
                                obs.get('color', 'black')
                            )
                        else:
                            continue

                        self.config_space.add_obstacle(obstacle)
                        self.renderer.add_obstacle(obstacle)

                # 加载起点和终点
                        # 加载起点和终点
                        if 'start' in data:
                            start_data = data['start']
                            self.control_panel.start_x_spin.setValue(start_data[0])
                            self.control_panel.start_y_spin.setValue(start_data[1])
                            self.renderer.set_start_point(start_data[0], start_data[1])
                            self._update_algorithms_start(start_data)

                        if 'goal' in data:
                            goal_data = data['goal']
                            self.control_panel.goal_x_spin.setValue(goal_data[0])
                            self.control_panel.goal_y_spin.setValue(goal_data[1])
                            self.renderer.set_goal_point(goal_data[0], goal_data[1])
                            self._update_algorithms_goal(goal_data)

                # 加载算法参数
                if 'algorithm' in data:
                    algo_index = self.control_panel.algorithm_combo.findText(data['algorithm'])
                    if algo_index >= 0:
                        self.control_panel.algorithm_combo.setCurrentIndex(algo_index)

                if 'parameters' in data:
                    params = data['parameters']
                    if 'step_size' in params:
                        self.control_panel.step_size_spin.setValue(params['step_size'])
                    if 'max_iter' in params:
                        self.control_panel.max_iter_spin.setValue(params['max_iter'])
                    if 'goal_sample_rate' in params:
                        self.control_panel.goal_sample_rate_spin.setValue(params['goal_sample_rate'])
                    if 'search_radius' in params:
                        self.control_panel.search_radius_spin.setValue(params['search_radius'])

                self.statusBar().showMessage(f"已加载文件: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法加载文件: {str(e)}")

    def _on_save(self):
        """保存文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "JSON文件 (*.json)"
        )

        if file_path:
            # 构建数据
            data = {
                'bounds': self.config_space.get_bounds(),
                'start': [
                    self.control_panel.start_x_spin.value(),
                    self.control_panel.start_y_spin.value()
                ],
                'goal': [
                    self.control_panel.goal_x_spin.value(),
                    self.control_panel.goal_y_spin.value()
                ],
                'algorithm': self.control_panel.algorithm_combo.currentText(),
                'parameters': {
                    'step_size': self.control_panel.step_size_spin.value(),
                    'max_iter': self.control_panel.max_iter_spin.value(),
                    'goal_sample_rate': self.control_panel.goal_sample_rate_spin.value(),
                    'search_radius': self.control_panel.search_radius_spin.value()
                },
                'obstacles': []
            }

            # 添加障碍物
            for obstacle in self.config_space.get_obstacles():
                if obstacle.get_type() == 'rectangle':
                    x, y, width, height = obstacle.get_boundary()
                    data['obstacles'].append({
                        'type': 'rectangle',
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'color': obstacle.color
                    })
                elif obstacle.get_type() == 'circle':
                    center_x, center_y, radius = obstacle.get_boundary()
                    data['obstacles'].append({
                        'type': 'circle',
                        'center_x': center_x,
                        'center_y': center_y,
                        'radius': radius,
                        'color': obstacle.color
                    })
                elif obstacle.get_type() == 'polygon':
                    vertices = obstacle.get_boundary()
                    data['obstacles'].append({
                        'type': 'polygon',
                        'vertices': vertices,
                        'color': obstacle.color
                    })

            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)

                self.statusBar().showMessage(f"已保存文件: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")

    def _on_export_image(self):
        """导出为图片"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出图片", "", "PNG图片 (*.png);;JPEG图片 (*.jpg);;所有文件 (*.*)"
        )

        if file_path:
            if self.renderer.save_as_image(file_path):
                self.statusBar().showMessage(f"已导出图片: {file_path}")
            else:
                QMessageBox.critical(self, "错误", "无法导出图片")

    def _on_export_csv(self):
        """导出结果为CSV"""
        if not self.current_algorithm.success:
            QMessageBox.warning(self, "警告", "没有可用的规划结果")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出CSV", "", "CSV文件 (*.csv)"
        )

        if file_path:
            try:
                # 获取算法详情
                details = self.current_algorithm.get_details()

                # 导出为CSV
                export_to_csv(details, self.current_algorithm.path, file_path)

                self.statusBar().showMessage(f"已导出CSV: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法导出CSV: {str(e)}")

    def _on_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于RRT算法可视化工具",
            "RRT算法可视化工具\n\n"
            "版本: 1.0.0\n"
            "一个用于可视化RRT路径规划算法的工具\n\n"
            "支持的算法:\n"
            "- 基础RRT\n"
            "- RRT*\n"
            "- RRT-Connect\n"
            "- Informed RRT*\n"
        )

    def _on_set_start(self):
        """设置起点"""
        x = self.control_panel.start_x_spin.value()
        y = self.control_panel.start_y_spin.value()

        # 更新渲染器
        self.renderer.set_start_point(x, y)

        # 更新算法起点
        self._update_algorithms_start([x, y])

        self.statusBar().showMessage(f"起点设置为 ({x}, {y})")

    def _on_set_goal(self):
        """设置终点"""
        x = self.control_panel.goal_x_spin.value()
        y = self.control_panel.goal_y_spin.value()

        # 更新渲染器
        self.renderer.set_goal_point(x, y)

        # 更新算法终点
        self._update_algorithms_goal([x, y])

        self.statusBar().showMessage(f"终点设置为 ({x}, {y})")

    def _update_algorithms_start(self, start):
        """更新所有算法的起点"""
        import numpy as np
        # 转换为NumPy数组
        start_np = np.array(start)
        for algorithm in self.algorithms.values():
            algorithm.start = start_np

    def _update_algorithms_goal(self, goal):
        """更新所有算法的终点"""
        import numpy as np
        # 转换为NumPy数组
        goal_np = np.array(goal)
        for algorithm in self.algorithms.values():
            algorithm.goal = goal_np

    def _on_add_rectangle(self):
        """添加矩形障碍物"""
        # 获取参数
        x = self.control_panel.obstacle_x_spin.value()
        y = self.control_panel.obstacle_y_spin.value()
        width = self.control_panel.obstacle_width_spin.value()
        height = self.control_panel.obstacle_height_spin.value()

        # 创建障碍物
        obstacle = RectangleObstacle(x, y, width, height)

        # 添加到配置空间
        self.config_space.add_obstacle(obstacle)

        # 添加到渲染器
        self.renderer.add_obstacle(obstacle)

        self.statusBar().showMessage(f"已添加矩形障碍物 at ({x}, {y})")

    def _on_add_circle(self):
        """添加圆形障碍物"""
        # 获取参数
        x = self.control_panel.obstacle_x_spin.value()
        y = self.control_panel.obstacle_y_spin.value()
        radius = self.control_panel.obstacle_radius_spin.value()

        # 创建障碍物
        obstacle = CircleObstacle(x, y, radius)

        # 添加到配置空间
        self.config_space.add_obstacle(obstacle)

        # 添加到渲染器
        self.renderer.add_obstacle(obstacle)

        self.statusBar().showMessage(f"已添加圆形障碍物 at ({x}, {y})")

    def _on_clear_obstacles(self):
        """清除所有障碍物"""
        # 清除配置空间中的障碍物
        self.config_space.clear_obstacles()

        # 清除渲染器中的障碍物
        self.renderer.clear_obstacles()

        self.statusBar().showMessage("已清除所有障碍物")

    def _on_algorithm_changed(self, index):
        """算法选择变化"""
        # 获取选中的算法名称
        algorithm_name = self.control_panel.algorithm_combo.currentText()

        # 更新当前算法
        self.current_algorithm = self.algorithms[algorithm_name]

        # 更新UI
        self._update_ui_for_algorithm(algorithm_name)

        self.statusBar().showMessage(f"已选择算法: {algorithm_name}")

    def _update_ui_for_algorithm(self, algorithm_name):
        """根据算法更新UI"""
        # 启用/禁用相关参数控制
        if algorithm_name == "RRTStar" or algorithm_name == "InformedRRT":
            self.control_panel.search_radius_label.setEnabled(True)
            self.control_panel.search_radius_spin.setEnabled(True)
            self.control_panel.goal_sample_rate_label.setEnabled(True)
            self.control_panel.goal_sample_rate_spin.setEnabled(True)
        elif algorithm_name == "RRTConnect":
            self.control_panel.search_radius_label.setEnabled(False)
            self.control_panel.search_radius_spin.setEnabled(False)
            self.control_panel.goal_sample_rate_label.setEnabled(False)
            self.control_panel.goal_sample_rate_spin.setEnabled(False)
        else:  # BaseRRT
            self.control_panel.search_radius_label.setEnabled(False)
            self.control_panel.search_radius_spin.setEnabled(False)
            self.control_panel.goal_sample_rate_label.setEnabled(True)
            self.control_panel.goal_sample_rate_spin.setEnabled(True)

    def _on_step_size_changed(self, value):
        """步长变化"""
        for algorithm in self.algorithms.values():
            algorithm.step_size = value

    def _on_max_iter_changed(self, value):
        """最大迭代次数变化"""
        for algorithm in self.algorithms.values():
            algorithm.max_iter = value

    def _on_goal_sample_rate_changed(self, value):
        """目标采样率变化"""
        for algorithm in self.algorithms.values():
            if hasattr(algorithm, 'goal_sample_rate'):
                algorithm.goal_sample_rate = value

    def _on_search_radius_changed(self, value):
        """搜索半径变化"""
        for algorithm in self.algorithms.values():
            if hasattr(algorithm, 'search_radius'):
                algorithm.search_radius = value

    def _on_animation_speed_changed(self, value):
        """动画速度变化"""
        # 计算定时器间隔（毫秒）
        # 值越大，间隔越小，动画越快
        interval = 1000 / (value + 1)  # 避免除以零

        if self.expansion_timer.isActive():
            self.expansion_timer.setInterval(int(interval))

    def _on_start(self):
        """开始规划"""
        if self.is_planning:
            return

        # 获取起点和终点坐标
        start_x = self.control_panel.start_x_spin.value()
        start_y = self.control_panel.start_y_spin.value()
        goal_x = self.control_panel.goal_x_spin.value()
        goal_y = self.control_panel.goal_y_spin.value()

        # 检查起点和终点是否设置
        if start_x is None or start_y is None or goal_x is None or goal_y is None:
            QMessageBox.warning(self, "警告", "请先设置起点和终点")
            return

        # 清除旧结果
        self.renderer.clear_tree()
        self.renderer.clear_path()

        # 设置为规划状态
        self.is_planning = True
        self.control_panel.start_button.setEnabled(False)
        self.control_panel.stop_button.setEnabled(True)

        # 执行算法
        self.statusBar().showMessage(f"正在执行算法: {self.current_algorithm.get_name()}...")

        # 如果开启动画，则使用动画模式
        if self.control_panel.animation_checkbox.isChecked():
            # 准备动画
            self.current_algorithm.reset()
            result = self.current_algorithm.plan()

            # 设置动画参数
            self.expansion_index = 0
            interval = 1000 / (self.control_panel.animation_speed_slider.value() + 1)
            self.expansion_timer.setInterval(int(interval))
            self.expansion_timer.start()
        else:
            # 直接执行算法
            result = self.current_algorithm.plan()

            # 可视化结果
            self.renderer.visualize_rrt(result)

            # 更新结果面板
            self.result_panel.update_results(self.current_algorithm.get_details())

            # 规划完成
            self._planning_finished()

    def _animate_expansion(self):
        """动画展示树的扩展过程"""
        try:
            # 获取扩展历史
            expansion_history = self.current_algorithm.expansion_history

            if self.expansion_index >= len(expansion_history):
                # 动画结束
                self.expansion_timer.stop()

                # 如果算法成功找到路径，则可视化
                if self.current_algorithm.success and self.current_algorithm.path and len(
                        self.current_algorithm.path) > 1:
                    for i in range(len(self.current_algorithm.path) - 1):
                        self.renderer.add_path_segment(
                            self.current_algorithm.path[i][0],
                            self.current_algorithm.path[i][1],
                            self.current_algorithm.path[i + 1][0],
                            self.current_algorithm.path[i + 1][1]
                        )

                # 更新结果面板
                self.result_panel.update_results(self.current_algorithm.get_details())

                # 规划完成
                self._planning_finished()
                return

            # 获取本次扩展的节点
            if expansion_history and self.expansion_index < len(expansion_history):
                from_idx, to_idx = expansion_history[self.expansion_index]

                # 安全检查 - 确保索引有效
                if (0 <= from_idx < len(self.current_algorithm.vertices) and
                        0 <= to_idx < len(self.current_algorithm.vertices)):
                    # 可视化扩展
                    self.renderer.visualize_expansion(from_idx, to_idx, self.current_algorithm.vertices)

            # 更新索引
            self.expansion_index += 1
        except Exception as e:
            # 出错时停止动画并显示错误信息
            self.expansion_timer.stop()
            import traceback
            print(f"动画展示过程中出错: {str(e)}")
            print(traceback.format_exc())
            self.statusBar().showMessage(f"错误: {str(e)}")
            self._planning_finished()

    def _planning_finished(self):
        """规划完成"""
        self.is_planning = False
        self.control_panel.start_button.setEnabled(True)
        self.control_panel.stop_button.setEnabled(False)

        # 更新状态栏
        if self.current_algorithm.success:
            self.statusBar().showMessage(
                f"规划成功! 路径长度: {self.current_algorithm.path_length:.2f}, "
                f"耗时: {self.current_algorithm.planning_time:.3f}秒"
            )
        else:
            self.statusBar().showMessage("规划失败，未找到有效路径")

    def _on_stop(self):
        """停止规划"""
        if not self.is_planning:
            return

        # 停止动画定时器
        if self.expansion_timer.isActive():
            self.expansion_timer.stop()

        # 重置规划状态
        self.is_planning = False
        self.control_panel.start_button.setEnabled(True)
        self.control_panel.stop_button.setEnabled(False)

        self.statusBar().showMessage("规划已停止")

    def _on_reset(self):
        """重置"""
        # 停止规划
        self._on_stop()

        # 清除渲染器
        self.renderer.clear()

        # 清除结果面板
        self.result_panel.clear_results()

        # 重置算法
        for algorithm in self.algorithms.values():
            algorithm.reset()

        self.statusBar().showMessage("已重置")