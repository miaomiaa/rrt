#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RRTVisualizer-Web - Web应用主文件
"""

import os
import json
import numpy as np
from flask import Flask, render_template, request, jsonify, abort, session, redirect, url_for
from functools import wraps

# 导入算法
from algorithms import BaseRRT, RRTStar, RRTConnect, InformedRRT
from environment import ConfigurationSpace, RectangleObstacle, CircleObstacle, PolygonObstacle, PRESETS
from utils.converter import numpy_to_list

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 更改为随机密钥
app.config['SESSION_TIMEOUT'] = 3600  # 会话超时时间（秒）
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


# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# 主页路由 - 只能有一个index函数
@app.route('/')
@login_required
def index():
    return render_template('index.html')


# 关于页面
@app.route('/about')
@login_required
def about():
    return render_template('about.html')


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 这里应该验证用户名和密码
    # 暂时使用简单验证
    if username and password:
        # 模拟用户验证成功
        session['user_id'] = 1
        session['username'] = username
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401


# 注册路由
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 这里应该验证并创建新用户
    # 暂时返回成功
    if username and email and password:
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': '注册失败'}), 400


# 登出路由
@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'success': True})


# 检查认证状态
@app.route('/api/check-auth')
def check_auth():
    """检查用户认证状态"""
    authenticated = 'user_id' in session
    return jsonify({'authenticated': authenticated})


# 获取用户信息
@app.route('/api/user-info')
@login_required
def user_info():
    """获取当前用户信息"""
    return jsonify({
        'id': session.get('user_id'),
        'username': session.get('username', '用户')
    })


# API: 执行规划
@app.route('/api/plan', methods=['POST'])
@login_required  # 添加登录验证
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