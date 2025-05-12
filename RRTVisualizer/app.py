#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RRTVisualizer-Web - Web应用主文件
一个基于Web的路径规划算法可视化应用程序
"""

import os
import json
import numpy as np
from flask import Flask, render_template, request, jsonify, abort

# 导入算法
from algorithms import BaseRRT, RRTStar, RRTConnect, InformedRRT
from environment import ConfigurationSpace, RectangleObstacle, CircleObstacle, PolygonObstacle, PRESETS
from utils.converter import numpy_to_list

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = 'rrt-visualizer-secret-key'
app.config['JSON_SORT_KEYS'] = False  # 保持JSON响应的键顺序

# 创建配置空间及算法实例
config_space = ConfigurationSpace(800, 600)
algorithms = {
    "BaseRRT": BaseRRT(
        [0, 0], [0, 0], config_space,
        step_size=20, goal_sample_rate=0.05, max_iter=1000
    ),
    "RRTStar": RRTStar(
        [0, 0], [0, 0], config_space,
        step_size=20, goal_sample_rate=0.05, max_iter=3000, search_radius=50
    ),
    "RRTConnect": RRTConnect(
        [0, 0], [0, 0], config_space,
        step_size=20, max_iter=1500
    ),
    "InformedRRT": InformedRRT(
        [0, 0], [0, 0], config_space,
        step_size=20, goal_sample_rate=0.05, max_iter=3000, search_radius=50
    )
}


# 主页
@app.route('/')
def index():
    return render_template('index.html')


# 关于页面
@app.route('/about')
def about():
    return render_template('about.html')


# API: 执行规划
@app.route('/api/plan', methods=['POST'])
def plan():
    try:
        # 获取请求数据
        data = request.json

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # 验证必需参数
        required_fields = ['start', 'goal', 'algorithm', 'obstacles', 'parameters']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # 提取参数
        start = data['start']
        goal = data['goal']
        algorithm_name = data['algorithm']
        obstacles_data = data['obstacles']
        parameters = data['parameters']

        # 验证算法名称
        if algorithm_name not in algorithms:
            return jsonify({'error': f'Unknown algorithm: {algorithm_name}'}), 400

        # 重置配置空间
        global config_space
        config_space = ConfigurationSpace(800, 600)

        # 添加障碍物
        for obs in obstacles_data:
            if obs['type'] == 'rectangle':
                obstacle = RectangleObstacle(
                    obs['x'], obs['y'], obs['width'], obs['height']
                )
            elif obs['type'] == 'circle':
                obstacle = CircleObstacle(
                    obs['centerX'], obs['centerY'], obs['radius']
                )
            else:
                continue

            config_space.add_obstacle(obstacle)

        # 更新算法参数
        algorithm = algorithms[algorithm_name]
        algorithm.start = np.array(start)
        algorithm.goal = np.array(goal)
        algorithm.config_space = config_space

        if 'stepSize' in parameters:
            algorithm.step_size = parameters['stepSize']
        if 'maxIter' in parameters:
            algorithm.max_iter = parameters['maxIter']
        if 'goalSampleRate' in parameters and hasattr(algorithm, 'goal_sample_rate'):
            algorithm.goal_sample_rate = parameters['goalSampleRate']
        if 'searchRadius' in parameters and hasattr(algorithm, 'search_radius'):
            algorithm.search_radius = parameters['searchRadius']

        # 执行规划
        result = algorithm.plan()

        # 转换NumPy数组为Python列表，以便JSON序列化
        serializable_result = numpy_to_list(result)

        # 添加算法详细信息到结果中
        serializable_result['details'] = numpy_to_list(algorithm.get_details())

        return jsonify(serializable_result)

    except Exception as e:
        app.logger.error(f"Error in plan endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


# API: 获取支持的算法
@app.route('/api/algorithms', methods=['GET'])
def get_algorithms():
    return jsonify(list(algorithms.keys()))


# API: 获取预设场景列表
@app.route('/api/presets', methods=['GET'])
def get_presets():
    preset_info = {}
    for key, preset in PRESETS.items():
        preset_info[key] = preset.get_metadata()
    return jsonify(preset_info)


# API: 获取特定预设场景
@app.route('/api/presets/<preset_id>', methods=['GET'])
def get_preset(preset_id):
    if preset_id not in PRESETS:
        return jsonify({'error': f'Unknown preset: {preset_id}'}), 404

    preset = PRESETS[preset_id]
    space = preset.create_space()

    # 收集场景信息
    obstacles = []
    for obs in space.obstacles:
        if obs.get_type() == 'rectangle':
            x, y, width, height = obs.get_boundary()
            obstacles.append({
                'type': 'rectangle',
                'x': x,
                'y': y,
                'width': width,
                'height': height
            })
        elif obs.get_type() == 'circle':
            centerX, centerY, radius = obs.get_boundary()
            obstacles.append({
                'type': 'circle',
                'centerX': centerX,
                'centerY': centerY,
                'radius': radius
            })

    # 构建响应
    response = {
        'metadata': preset.get_metadata(),
        'obstacles': obstacles
    }

    return jsonify(response)


# 启动应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)