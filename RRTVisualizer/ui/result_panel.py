"""
结果面板类，显示算法运行结果和统计信息
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QTextEdit,
    QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView
)


class ResultPanel(QWidget):
    """RRT算法结果面板"""

    def __init__(self, parent=None):
        """初始化结果面板"""
        super().__init__(parent)

        # 设置样式
        self.setMinimumWidth(300)

        # 创建布局
        self._init_layout()

    def _init_layout(self):
        """初始化布局"""
        main_layout = QVBoxLayout(self)

        # 结果摘要
        summary_group = QGroupBox("结果摘要")
        main_layout.addWidget(summary_group)

        summary_layout = QFormLayout(summary_group)

        # 算法名称
        self.algorithm_name_label = QLabel("--")
        summary_layout.addRow("算法:", self.algorithm_name_label)

        # 路径长度
        self.path_length_label = QLabel("--")
        summary_layout.addRow("路径长度:", self.path_length_label)

        # 规划时间
        self.planning_time_label = QLabel("--")
        summary_layout.addRow("规划时间:", self.planning_time_label)

        # 迭代次数
        self.iterations_label = QLabel("--")
        summary_layout.addRow("迭代次数:", self.iterations_label)

        # 节点数量
        self.nodes_count_label = QLabel("--")
        summary_layout.addRow("节点数量:", self.nodes_count_label)

        # 是否成功
        self.success_label = QLabel("--")
        summary_layout.addRow("是否成功:", self.success_label)

        # 详细信息
        details_group = QGroupBox("详细信息")
        main_layout.addWidget(details_group)

        details_layout = QVBoxLayout(details_group)

        # 创建表格
        self.details_table = QTableWidget(0, 2)
        self.details_table.setHorizontalHeaderLabels(["参数", "值"])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        details_layout.addWidget(self.details_table)

    def update_results(self, results):
        """
        更新结果显示

        参数:
            results: 结果字典
        """
        try:
            if not results or not isinstance(results, dict):
                print("警告：结果数据无效")
                return

            # 更新摘要信息
            self.algorithm_name_label.setText(results.get("name", "--"))

            # 安全转换数值，防止出现异常
            try:
                path_length = float(results.get('path_length', 0))
                self.path_length_label.setText(f"{path_length:.2f}")
            except (ValueError, TypeError):
                self.path_length_label.setText("--")

            try:
                planning_time = float(results.get('planning_time', 0))
                self.planning_time_label.setText(f"{planning_time:.3f} 秒")
            except (ValueError, TypeError):
                self.planning_time_label.setText("--")

            self.iterations_label.setText(str(results.get("iterations", 0)))
            self.nodes_count_label.setText(str(results.get("nodes", 0)))
            self.success_label.setText("是" if results.get("success", False) else "否")

            # 更新详细信息表格
            self.details_table.setRowCount(0)

            for key, value in results.items():
                # 跳过已在摘要中显示的字段
                if key in ["name", "path_length", "planning_time", "iterations", "nodes", "success"]:
                    continue

                # 跳过复杂对象，防止转换为字符串时出错
                if isinstance(value, (list, dict)) and len(str(value)) > 1000:
                    value = f"[复杂数据，长度：{len(str(value))}]"

                # 添加新行
                row = self.details_table.rowCount()
                self.details_table.insertRow(row)

                # 参数名
                param_item = QTableWidgetItem(str(key))
                param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
                self.details_table.setItem(row, 0, param_item)

                # 参数值
                value_str = str(value)
                if isinstance(value, float):
                    try:
                        value_str = f"{value:.4f}"
                    except:
                        pass

                value_item = QTableWidgetItem(value_str)
                value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
                self.details_table.setItem(row, 1, value_item)
        except Exception as e:
            import traceback
            print(f"更新结果面板时出错: {str(e)}")
            print(traceback.format_exc())

    def clear_results(self):
        """清除结果"""
        # 清除摘要信息
        self.algorithm_name_label.setText("--")
        self.path_length_label.setText("--")
        self.planning_time_label.setText("--")
        self.iterations_label.setText("--")
        self.nodes_count_label.setText("--")
        self.success_label.setText("--")

        # 清除详细信息表格
        self.details_table.setRowCount(0)