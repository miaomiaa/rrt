"""
控制面板类，提供算法参数设置和控制按钮
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLabel, QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QSlider, QCheckBox, QTabWidget
)


class ControlPanel(QWidget):
    """RRT算法控制面板"""

    def __init__(self, parent=None):
        """初始化控制面板"""
        super().__init__(parent)

        # 设置样式
        self.setMinimumWidth(300)

        # 创建布局
        self._init_layout()

    def _init_layout(self):
        """初始化布局"""
        main_layout = QVBoxLayout(self)

        # 创建选项卡
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # 算法选项卡
        algorithm_tab = QWidget()
        tab_widget.addTab(algorithm_tab, "算法")

        # 环境选项卡
        environment_tab = QWidget()
        tab_widget.addTab(environment_tab, "环境")

        # 初始化算法选项卡
        self._init_algorithm_tab(algorithm_tab)

        # 初始化环境选项卡
        self._init_environment_tab(environment_tab)

        # 控制按钮
        control_group = QGroupBox("控制")
        main_layout.addWidget(control_group)

        control_layout = QVBoxLayout(control_group)

        # 按钮布局
        button_layout = QHBoxLayout()
        control_layout.addLayout(button_layout)

        # 开始按钮
        self.start_button = QPushButton("开始规划")
        button_layout.addWidget(self.start_button)

        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        # 重置按钮
        self.reset_button = QPushButton("重置")
        button_layout.addWidget(self.reset_button)

        # 动画控制
        animation_layout = QHBoxLayout()
        control_layout.addLayout(animation_layout)

        # 动画复选框
        self.animation_checkbox = QCheckBox("启用动画")
        self.animation_checkbox.setChecked(True)
        animation_layout.addWidget(self.animation_checkbox)

        # 动画速度滑块
        animation_speed_layout = QHBoxLayout()
        control_layout.addLayout(animation_speed_layout)

        animation_speed_layout.addWidget(QLabel("动画速度:"))

        self.animation_speed_slider = QSlider(Qt.Horizontal)
        self.animation_speed_slider.setMinimum(1)
        self.animation_speed_slider.setMaximum(100)
        self.animation_speed_slider.setValue(30)
        animation_speed_layout.addWidget(self.animation_speed_slider)

    def _init_algorithm_tab(self, tab):
        """初始化算法选项卡"""
        layout = QVBoxLayout(tab)

        # 算法选择
        algorithm_group = QGroupBox("算法选择")
        layout.addWidget(algorithm_group)

        algorithm_layout = QFormLayout(algorithm_group)

        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["BaseRRT", "RRTStar", "RRTConnect", "InformedRRT"])
        algorithm_layout.addRow("算法:", self.algorithm_combo)

        # 算法参数
        parameters_group = QGroupBox("算法参数")
        layout.addWidget(parameters_group)

        parameters_layout = QFormLayout(parameters_group)

        # 步长
        self.step_size_spin = QDoubleSpinBox()
        self.step_size_spin.setRange(1.0, 100.0)
        self.step_size_spin.setValue(20.0)
        self.step_size_spin.setSingleStep(1.0)
        parameters_layout.addRow("步长:", self.step_size_spin)

        # 最大迭代次数
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(100, 10000)
        self.max_iter_spin.setValue(1000)
        self.max_iter_spin.setSingleStep(100)
        parameters_layout.addRow("最大迭代次数:", self.max_iter_spin)

        # 目标采样率
        self.goal_sample_rate_label = QLabel("目标采样率:")
        self.goal_sample_rate_spin = QDoubleSpinBox()
        self.goal_sample_rate_spin.setRange(0.0, 1.0)
        self.goal_sample_rate_spin.setValue(0.05)
        self.goal_sample_rate_spin.setSingleStep(0.01)
        parameters_layout.addRow(self.goal_sample_rate_label, self.goal_sample_rate_spin)

        # 搜索半径
        self.search_radius_label = QLabel("搜索半径:")
        self.search_radius_spin = QDoubleSpinBox()
        self.search_radius_spin.setRange(1.0, 200.0)
        self.search_radius_spin.setValue(50.0)
        self.search_radius_spin.setSingleStep(1.0)
        parameters_layout.addRow(self.search_radius_label, self.search_radius_spin)

        # 默认禁用特定算法参数
        self.search_radius_label.setEnabled(False)
        self.search_radius_spin.setEnabled(False)

    def _init_environment_tab(self, tab):
        """初始化环境选项卡"""
        layout = QVBoxLayout(tab)

        # 起点和终点
        points_group = QGroupBox("起点和终点")
        layout.addWidget(points_group)

        points_layout = QFormLayout(points_group)

        # 起点
        start_layout = QHBoxLayout()

        self.start_x_spin = QSpinBox()
        self.start_x_spin.setRange(0, 800)
        self.start_x_spin.setValue(50)
        start_layout.addWidget(QLabel("X:"))
        start_layout.addWidget(self.start_x_spin)

        self.start_y_spin = QSpinBox()
        self.start_y_spin.setRange(0, 600)
        self.start_y_spin.setValue(50)
        start_layout.addWidget(QLabel("Y:"))
        start_layout.addWidget(self.start_y_spin)

        points_layout.addRow("起点:", start_layout)

        self.set_start_button = QPushButton("设置起点")
        points_layout.addRow("", self.set_start_button)

        # 终点
        goal_layout = QHBoxLayout()

        self.goal_x_spin = QSpinBox()
        self.goal_x_spin.setRange(0, 800)
        self.goal_x_spin.setValue(750)
        goal_layout.addWidget(QLabel("X:"))
        goal_layout.addWidget(self.goal_x_spin)

        self.goal_y_spin = QSpinBox()
        self.goal_y_spin.setRange(0, 600)
        self.goal_y_spin.setValue(550)
        goal_layout.addWidget(QLabel("Y:"))
        goal_layout.addWidget(self.goal_y_spin)

        points_layout.addRow("终点:", goal_layout)

        self.set_goal_button = QPushButton("设置终点")
        points_layout.addRow("", self.set_goal_button)

        # 障碍物
        obstacles_group = QGroupBox("障碍物")
        layout.addWidget(obstacles_group)

        obstacles_layout = QFormLayout(obstacles_group)

        # 障碍物位置和大小
        obs_pos_layout = QHBoxLayout()

        self.obstacle_x_spin = QSpinBox()
        self.obstacle_x_spin.setRange(0, 800)
        self.obstacle_x_spin.setValue(400)
        obs_pos_layout.addWidget(QLabel("X:"))
        obs_pos_layout.addWidget(self.obstacle_x_spin)

        self.obstacle_y_spin = QSpinBox()
        self.obstacle_y_spin.setRange(0, 600)
        self.obstacle_y_spin.setValue(300)
        obs_pos_layout.addWidget(QLabel("Y:"))
        obs_pos_layout.addWidget(self.obstacle_y_spin)

        obstacles_layout.addRow("位置:", obs_pos_layout)

        obs_size_layout = QHBoxLayout()

        self.obstacle_width_spin = QSpinBox()
        self.obstacle_width_spin.setRange(1, 800)
        self.obstacle_width_spin.setValue(100)
        obs_size_layout.addWidget(QLabel("宽:"))
        obs_size_layout.addWidget(self.obstacle_width_spin)

        self.obstacle_height_spin = QSpinBox()
        self.obstacle_height_spin.setRange(1, 600)
        self.obstacle_height_spin.setValue(100)
        obs_size_layout.addWidget(QLabel("高:"))
        obs_size_layout.addWidget(self.obstacle_height_spin)

        obstacles_layout.addRow("大小:", obs_size_layout)

        # 圆形障碍物半径
        self.obstacle_radius_spin = QSpinBox()
        self.obstacle_radius_spin.setRange(1, 400)
        self.obstacle_radius_spin.setValue(50)
        obstacles_layout.addRow("半径:", self.obstacle_radius_spin)

        # 障碍物按钮
        obs_buttons_layout = QHBoxLayout()

        self.add_rectangle_button = QPushButton("添加矩形")
        obs_buttons_layout.addWidget(self.add_rectangle_button)

        self.add_circle_button = QPushButton("添加圆形")
        obs_buttons_layout.addWidget(self.add_circle_button)

        obstacles_layout.addRow("", obs_buttons_layout)

        self.clear_obstacles_button = QPushButton("清除所有障碍物")
        obstacles_layout.addRow("", self.clear_obstacles_button)