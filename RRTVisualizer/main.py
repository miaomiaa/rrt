#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RRTVisualizer - 主程序入口
一个用于路径规划算法可视化的应用程序
"""

import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# 全局异常处理器
def excepthook(exc_type, exc_value, exc_traceback):
    """
    捕获未处理的异常并显示错误信息
    """
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"未捕获的异常:\n{error_msg}")

    # 如果GUI已经初始化，则显示错误对话框
    app = QApplication.instance()
    if app:
        QMessageBox.critical(None, "错误", f"程序出现未处理的异常:\n{str(exc_value)}\n\n"
                                           f"详细信息已写入控制台")

    # 写入日志文件
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(f"===== {os.path.basename(sys.argv[0])} 异常 =====\n")
        f.write(error_msg)
        f.write("\n\n")


# 设置全局异常处理器
sys.excepthook = excepthook


def main():
    """程序主入口函数"""
    try:
        from ui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("RRTVisualizer")

        # 创建并显示主窗口
        window = MainWindow()
        window.show()

        return app.exec_()
    except Exception as e:
        traceback.print_exc()
        print(f"程序启动失败: {str(e)}")

        # 终端环境下保持窗口
        if not QApplication.instance():
            input("按Enter键退出...")
        return 1


if __name__ == "__main__":
    sys.exit(main())