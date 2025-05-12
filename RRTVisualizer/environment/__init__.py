"""
环境模块
包含配置空间和障碍物定义
"""

from .obstacles import Obstacle, RectangleObstacle, CircleObstacle, PolygonObstacle
from .space import ConfigurationSpace
from .presets import PRESETS, ScenePreset

# 导出所有环境相关类
__all__ = [
    'Obstacle',
    'RectangleObstacle',
    'CircleObstacle',
    'PolygonObstacle',
    'ConfigurationSpace',
    'PRESETS',
    'ScenePreset'
]