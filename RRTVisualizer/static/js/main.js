/**
 * 主要JavaScript文件
 * 处理用户交互和界面逻辑
 */

// 确保脚本加载和执行
window.mainJsLoaded = true;

document.addEventListener('DOMContentLoaded', function() {

    console.log('DOM Content Loaded - Initializing RRT Visualizer');
// 获取预设场景相关元素
const presetSceneSelect = document.getElementById('presetSceneSelect');
const presetDescription = document.getElementById('presetDescription');
const loadPresetBtn = document.getElementById('loadPresetBtn');

// 更新场景描述
if (presetSceneSelect) {
    presetSceneSelect.addEventListener('change', () => {
        const selectedValue = presetSceneSelect.value;
        if (!selectedValue) {
            presetDescription.textContent = '';
            return;
        }

        // 获取预设场景描述
        fetch(`/api/presets/${selectedValue}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络错误: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                if (data.metadata && data.metadata.description) {
                    presetDescription.textContent = data.metadata.description;
                } else {
                    presetDescription.textContent = '';
                }
            })
            .catch(error => {
                console.error('获取预设场景描述出错:', error);
                presetDescription.textContent = '';
            });
    });
}

// 加载预设场景
if (loadPresetBtn) {
    loadPresetBtn.addEventListener('click', () => {
        const selectedValue = presetSceneSelect.value;
        if (!selectedValue) {
            showToast('错误', '请先选择一个预设场景', 'error');
            return;
        }

        // 显示加载动画
        if (loadingOverlay) {
            loadingOverlay.classList.remove('d-none');
        }

        // 获取预设场景数据
        fetch(`/api/presets/${selectedValue}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络错误: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                // 隐藏加载动画
                if (loadingOverlay) {
                    loadingOverlay.classList.add('d-none');
                }

                // 清除现有环境
                if (visualizer) {
                    visualizer.clearObstacles();
                }

                // 设置起点和终点
                if (data.metadata && data.metadata.suggested_start && data.metadata.suggested_goal) {
                    const start = data.metadata.suggested_start;
                    const goal = data.metadata.suggested_goal;

                    if (visualizer) {
                        visualizer.setStart(start[0], start[1]);
                        visualizer.setGoal(goal[0], goal[1]);
                    }

                    // 更新输入框
                    if (startXInput) startXInput.value = Math.floor(start[0]);
                    if (startYInput) startYInput.value = Math.floor(start[1]);
                    if (goalXInput) goalXInput.value = Math.floor(goal[0]);
                    if (goalYInput) goalYInput.value = Math.floor(goal[1]);
                }

                // 添加障碍物
                if (data.obstacles && visualizer) {
                    for (const obstacle of data.obstacles) {
                        if (obstacle.type === 'rectangle') {
                            visualizer.addRectangleObstacle(
                                obstacle.x, obstacle.y,
                                obstacle.width, obstacle.height
                            );
                        } else if (obstacle.type === 'circle') {
                            visualizer.addCircleObstacle(
                                obstacle.centerX, obstacle.centerY,
                                obstacle.radius
                            );
                        }
                    }
                }

                showToast('场景已加载', `已成功加载"${presetSceneSelect.options[presetSceneSelect.selectedIndex].text}"场景`, 'success');
            })
            .catch(error => {
                // 隐藏加载动画
                if (loadingOverlay) {
                    loadingOverlay.classList.add('d-none');
                }

                console.error('加载预设场景出错:', error);
                showToast('加载失败', '无法加载预设场景，请重试', 'error');
            });
    });
}
    // 检查依赖项是否加载
    setTimeout(function() {
        if (typeof RRTVisualizer === 'undefined') {
            console.error('RRTVisualizer class not found - using fallback');
            showError('可视化组件加载失败，部分功能可能不可用');
        } else {
            // 显示欢迎提示
            showWelcomeToast();
        }
    }, 1000);

    // 初始化工具提示
    initializeTooltips();

    // 创建可视化器实例
    let visualizer;
    try {
        visualizer = new RRTVisualizer('rrtCanvas');
        console.log('Visualizer instance created');
        window.visualizerInitialized = true;
        window.visualizer = visualizer; // 存储全局引用
    } catch(e) {
        console.error('Failed to create visualizer:', e);
        showError('初始化可视化组件失败');
        return; // 如果创建失败，不继续执行
    }

    // 获取UI元素
    const algorithmSelect = document.getElementById('algorithmSelect');
    const stepSizeSlider = document.getElementById('stepSize');
    const stepSizeValue = document.getElementById('stepSizeValue');
    const maxIterationsSlider = document.getElementById('maxIterations');
    const maxIterationsValue = document.getElementById('maxIterationsValue');
    const goalSampleRateSlider = document.getElementById('goalSampleRate');
    const goalSampleRateValue = document.getElementById('goalSampleRateValue');
    const searchRadiusSlider = document.getElementById('searchRadius');
    const searchRadiusValue = document.getElementById('searchRadiusValue');
    const goalSampleRateContainer = document.getElementById('goalSampleRateContainer');
    const searchRadiusContainer = document.getElementById('searchRadiusContainer');

    const startXInput = document.getElementById('startX');
    const startYInput = document.getElementById('startY');
    const goalXInput = document.getElementById('goalX');
    const goalYInput = document.getElementById('goalY');
    const setStartBtn = document.getElementById('setStartBtn');
    const setGoalBtn = document.getElementById('setGoalBtn');

    const rectXInput = document.getElementById('rectX');
    const rectYInput = document.getElementById('rectY');
    const rectWidthInput = document.getElementById('rectWidth');
    const rectHeightInput = document.getElementById('rectHeight');
    const addRectBtn = document.getElementById('addRectBtn');

    const circleXInput = document.getElementById('circleX');
    const circleYInput = document.getElementById('circleY');
    const circleRadiusInput = document.getElementById('circleRadius');
    const addCircleBtn = document.getElementById('addCircleBtn');

    const clearObstaclesBtn = document.getElementById('clearObstaclesBtn');
    const startBtn = document.getElementById('startBtn');
    const resetBtn = document.getElementById('resetBtn');
    const exportImageBtn = document.getElementById('exportImageBtn');
    const exportResultBtn = document.getElementById('exportResultBtn');

    const loadingOverlay = document.getElementById('loadingOverlay');

    // 结果面板元素
    const resultAlgorithm = document.getElementById('resultAlgorithm');
    const resultPathLength = document.getElementById('resultPathLength');
    const resultPlanningTime = document.getElementById('resultPlanningTime');
    const resultIterations = document.getElementById('resultIterations');
    const resultNodes = document.getElementById('resultNodes');
    const resultSuccess = document.getElementById('resultSuccess');
    const resultDetailsTable = document.getElementById('resultDetailsTable');

    // 为所有按钮添加波纹效果
    try {
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', function(e) {
                const ripple = document.createElement('span');
                ripple.classList.add('ripple');
                this.appendChild(ripple);

                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);

                ripple.style.width = ripple.style.height = `${size}px`;
                ripple.style.left = `${e.clientX - rect.left - size/2}px`;
                ripple.style.top = `${e.clientY - rect.top - size/2}px`;

                ripple.classList.add('active');

                setTimeout(() => {
                    ripple.remove();
                }, 600);
            });
        });
    } catch (error) {
        console.warn('Button ripple effect could not be applied:', error);
    }

    // 更新滑块值显示
    if (stepSizeSlider && stepSizeValue) {
        stepSizeSlider.addEventListener('input', () => {
            stepSizeValue.textContent = stepSizeSlider.value;
            stepSizeValue.classList.add('highlight');
            setTimeout(() => stepSizeValue.classList.remove('highlight'), 300);
        });
    }

    if (maxIterationsSlider && maxIterationsValue) {
        maxIterationsSlider.addEventListener('input', () => {
            maxIterationsValue.textContent = maxIterationsSlider.value;
            maxIterationsValue.classList.add('highlight');
            setTimeout(() => maxIterationsValue.classList.remove('highlight'), 300);
        });
    }

    if (goalSampleRateSlider && goalSampleRateValue) {
        goalSampleRateSlider.addEventListener('input', () => {
            goalSampleRateValue.textContent = goalSampleRateSlider.value;
            goalSampleRateValue.classList.add('highlight');
            setTimeout(() => goalSampleRateValue.classList.remove('highlight'), 300);
        });
    }

    if (searchRadiusSlider && searchRadiusValue) {
        searchRadiusSlider.addEventListener('input', () => {
            searchRadiusValue.textContent = searchRadiusSlider.value;
            searchRadiusValue.classList.add('highlight');
            setTimeout(() => searchRadiusValue.classList.remove('highlight'), 300);
        });
    }

    // 根据选择的算法显示/隐藏相关参数
    if (algorithmSelect) {
        algorithmSelect.addEventListener('change', () => {
            updateAlgorithmParameters();
            showAlgorithmInfo(algorithmSelect.value);
        });
    }

    function updateAlgorithmParameters() {
        if (!algorithmSelect || !goalSampleRateContainer || !searchRadiusContainer) return;

        const selectedAlgorithm = algorithmSelect.value;

        // 控制目标采样率参数的显示
        if (selectedAlgorithm === 'RRTConnect') {
            fadeOut(goalSampleRateContainer, () => {
                goalSampleRateContainer.style.display = 'none';
            });
        } else {
            goalSampleRateContainer.style.display = 'block';
            fadeIn(goalSampleRateContainer);
        }

        // 控制搜索半径参数的显示
        if (selectedAlgorithm === 'RRTStar' || selectedAlgorithm === 'InformedRRT') {
            searchRadiusContainer.style.display = 'block';
            fadeIn(searchRadiusContainer);
        } else {
            fadeOut(searchRadiusContainer, () => {
                searchRadiusContainer.style.display = 'none';
            });
        }
    }

    // 初始化参数显示
    updateAlgorithmParameters();

    // 显示算法信息
    function showAlgorithmInfo(algorithm) {
        if (!algorithm) return;

        let title, description;

        switch(algorithm) {
            case 'BaseRRT':
                title = '基础RRT算法';
                description = '这是最基本的RRT算法，通过随机采样和树扩展来探索空间。简单且效率适中，但生成的路径通常不是最优的。';
                break;
            case 'RRTStar':
                title = 'RRT*算法';
                description = 'RRT的优化版本，通过重布线和重组树结构来提高路径质量。随着迭代次数增加，路径会逐渐接近最优解。';
                break;
            case 'RRTConnect':
                title = 'RRT-Connect算法';
                description = '双向RRT算法，从起点和终点同时扩展树，当两棵树相遇时即找到路径。特别适合没有复杂约束的场景，收敛速度快。';
                break;
            case 'InformedRRT':
                title = 'Informed RRT*算法';
                description = 'RRT*的进一步优化，当找到初始解后，使用椭圆采样空间来聚焦搜索，加速收敛到最优解。在复杂环境中特别有效。';
                break;
            default:
                title = '未知算法';
                description = '没有关于此算法的详细信息。';
        }

        // 显示一个提示框
        showToast(title, description);
    }

    // 手动输入坐标设置起点
    if (startXInput && startYInput) {
        startXInput.addEventListener('change', function() {
            updateStartFromInputs();
        });

        startYInput.addEventListener('change', function() {
            updateStartFromInputs();
        });
    }

    // 手动输入坐标设置终点
    if (goalXInput && goalYInput) {
        goalXInput.addEventListener('change', function() {
            updateGoalFromInputs();
        });

        goalYInput.addEventListener('change', function() {
            updateGoalFromInputs();
        });
    }

    // 从输入框更新起点
    function updateStartFromInputs() {
        if (!visualizer) return;

        const x = Number(startXInput.value);
        const y = Number(startYInput.value);

        if (!isNaN(x) && !isNaN(y)) {
            visualizer.setStart(x, y);
            pulseElement(startXInput.parentElement);
            pulseElement(startYInput.parentElement);
            console.log('从输入框更新起点:', x, y);
        }
    }

    // 从输入框更新终点
    function updateGoalFromInputs() {
        if (!visualizer) return;

        const x = Number(goalXInput.value);
        const y = Number(goalYInput.value);

        if (!isNaN(x) && !isNaN(y)) {
            visualizer.setGoal(x, y);
            pulseElement(goalXInput.parentElement);
            pulseElement(goalYInput.parentElement);
            console.log('从输入框更新终点:', x, y);
        }
    }

    // 设置起点
    if (setStartBtn) {
        setStartBtn.addEventListener('click', () => {
            if (!visualizer) {
                showToast('错误', '可视化组件未初始化', 'error');
                return;
            }

            const x = Number(startXInput.value);
            const y = Number(startYInput.value);
            console.log('Setting start in UI:', x, y);

            // 如果提供了坐标，直接设置，否则进入点击模式
            if (!isNaN(x) && !isNaN(y)) {
                visualizer.setStart(x, y);
                showToast('起点已设置', `起点已设置在 (${x}, ${y})`);
            } else {
                // 进入起点设置模式，等待用户点击
                visualizer.enterSetStartMode();
                showToast('设置起点模式', '请在画布上点击以设置起点位置');
            }
        });
    }

    // 设置终点
    if (setGoalBtn) {
        setGoalBtn.addEventListener('click', () => {
            if (!visualizer) {
                showToast('错误', '可视化组件未初始化', 'error');
                return;
            }

            const x = Number(goalXInput.value);
            const y = Number(goalYInput.value);
            console.log('Setting goal in UI:', x, y);

            // 如果提供了坐标，直接设置，否则进入点击模式
            if (!isNaN(x) && !isNaN(y)) {
                visualizer.setGoal(x, y);
                showToast('终点已设置', `终点已设置在 (${x}, ${y})`);
            } else {
                // 进入终点设置模式，等待用户点击
                visualizer.enterSetGoalMode();
                showToast('设置终点模式', '请在画布上点击以设置终点位置');
            }
        });
    }

    // 添加矩形障碍物
    if (addRectBtn) {
        addRectBtn.addEventListener('click', () => {
            if (!visualizer) {
                showToast('错误', '可视化组件未初始化', 'error');
                return;
            }

            const x = Number(rectXInput.value);
            const y = Number(rectYInput.value);
            const width = Number(rectWidthInput.value);
            const height = Number(rectHeightInput.value);

            if (isNaN(x) || isNaN(y) || isNaN(width) || isNaN(height)) {
                showToast('参数错误', '请输入有效的矩形参数', 'error');
                return;
            }

            try {
                visualizer.addRectangleObstacle(x, y, width, height);
                showToast('已添加障碍物', `已添加矩形障碍物：(${x}, ${y}, ${width}, ${height})`);
            } catch (error) {
                console.error('添加矩形障碍物失败:', error);
                showToast('添加障碍物失败', '操作过程中出现错误', 'error');
            }
        });
    }

    // 添加圆形障碍物
    if (addCircleBtn) {
        addCircleBtn.addEventListener('click', () => {
            if (!visualizer) {
                showToast('错误', '可视化组件未初始化', 'error');
                return;
            }

            const centerX = Number(circleXInput.value);
            const centerY = Number(circleYInput.value);
            const radius = Number(circleRadiusInput.value);

            if (isNaN(centerX) || isNaN(centerY) || isNaN(radius)) {
                showToast('参数错误', '请输入有效的圆形参数', 'error');
                return;
            }

            try {
                visualizer.addCircleObstacle(centerX, centerY, radius);
                showToast('已添加障碍物', `已添加圆形障碍物：中心(${centerX}, ${centerY})，半径${radius}`);
            } catch (error) {
                console.error('添加圆形障碍物失败:', error);
                showToast('添加障碍物失败', '操作过程中出现错误', 'error');
            }
        });
    }

    // 清除障碍物
    if (clearObstaclesBtn) {
        clearObstaclesBtn.addEventListener('click', () => {
            if (!visualizer) {
                showToast('错误', '可视化组件未初始化', 'error');
                return;
            }

            try {
                visualizer.clearObstacles();
                showToast('障碍物已清除', '所有障碍物已被移除');
            } catch (error) {
                console.error('清除障碍物失败:', error);
                showToast('清除障碍物失败', '操作过程中出现错误', 'error');
            }
        });
    }

    // 重置所有内容
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (!visualizer) {
                showToast('错误', '可视化组件未初始化', 'error');
                return;
            }

            try {
                visualizer.reset();
                clearResultDisplay();
                showToast('已重置', '环境和结果已重置');
            } catch (error) {
                console.error('重置失败:', error);
                showToast('重置失败', '操作过程中出现错误', 'error');
            }
        });
    }

    // 执行规划
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            if (!visualizer) {
                showToast('错误', '可视化组件未初始化', 'error');
                return;
            }

            // 检查起点和终点是否已设置
            if (!visualizer.state.start || !visualizer.state.goal) {
                showToast('设置错误', '请先设置起点和终点！', 'error');
                return;
            }

            // 显示加载动画
            if (loadingOverlay) {
                loadingOverlay.classList.remove('d-none');
            }

            // 添加按钮动画
            if (startBtn) {
                startBtn.classList.add('active');
            }

            // 准备请求数据
            const requestData = {
                start: [visualizer.state.start.x, visualizer.state.start.y],
                goal: [visualizer.state.goal.x, visualizer.state.goal.y],
                algorithm: algorithmSelect ? algorithmSelect.value : 'BaseRRT',
                obstacles: visualizer.state.obstacles.map(obstacle => {
                    if (obstacle.type === 'rectangle') {
                        return {
                            type: 'rectangle',
                            x: obstacle.x,
                            y: obstacle.y,
                            width: obstacle.width,
                            height: obstacle.height
                        };
                    } else if (obstacle.type === 'circle') {
                        return {
                            type: 'circle',
                            centerX: obstacle.centerX,
                            centerY: obstacle.centerY,
                            radius: obstacle.radius
                        };
                    }
                    return obstacle;
                }),
                parameters: {
                    stepSize: stepSizeSlider ? Number(stepSizeSlider.value) : 20,
                    maxIter: maxIterationsSlider ? Number(maxIterationsSlider.value) : 1000,
                    goalSampleRate: goalSampleRateSlider ? Number(goalSampleRateSlider.value) : 0.05,
                    searchRadius: searchRadiusSlider ? Number(searchRadiusSlider.value) : 50
                }
            };

            // 发送规划请求
            fetch('/api/plan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络错误: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                // 隐藏加载动画
                if (loadingOverlay) {
                    loadingOverlay.classList.add('d-none');
                }

                // 移除按钮动画
                if (startBtn) {
                    startBtn.classList.remove('active');
                }

                // 处理错误
                if (data.error) {
                    showToast('规划出错', data.error, 'error');
                    return;
                }

                try {
                    // 更新可视化
                    visualizer.updateResult(data);

                    // 更新结果面板
                    updateResultDisplay(data);

                    // 显示成功消息
                    if (data.success) {
                        showToast('规划成功', `使用${algorithmSelect ? algorithmSelect.value : 'BaseRRT'}算法找到路径，长度: ${formatNumber(data.details.path_length)}`);
                    } else {
                        showToast('规划未成功', '未能找到路径，请尝试调整参数或修改环境', 'warning');
                    }
                } catch (error) {
                    console.error('处理结果时出错:', error);
                    showToast('处理结果出错', '无法显示规划结果', 'error');
                }
            })
            .catch(error => {
                // 隐藏加载动画
                if (loadingOverlay) {
                    loadingOverlay.classList.add('d-none');
                }

                // 移除按钮动画
                if (startBtn) {
                    startBtn.classList.remove('active');
                }

                // 显示错误信息
                showToast('请求出错', error.message, 'error');
                console.error('请求出错:', error);
            });
        });
    }

    // 导出为图片
    if (exportImageBtn) {
        exportImageBtn.addEventListener('click', () => {
            if (!visualizer) {
                showToast('错误', '可视化组件未初始化', 'error');
                return;
            }

            try {
                const dataUrl = visualizer.exportToImage();
                if (!dataUrl) {
                    showToast('导出失败', '无法导出图片', 'error');
                    return;
                }

                // 创建下载链接
                const downloadLink = document.createElement('a');
                downloadLink.href = dataUrl;
                downloadLink.download = `RRT_${algorithmSelect ? algorithmSelect.value : 'BaseRRT'}_${new Date().toISOString().slice(0, 10)}.png`;
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);

                showToast('导出成功', '图片已成功导出');
            } catch (error) {
                console.error('导出图片失败:', error);
                showToast('导出失败', '无法导出图片', 'error');
            }
        });
    }

    // 导出结果数据
    if (exportResultBtn) {
        exportResultBtn.addEventListener('click', () => {
            try {
                // 检查是否有结果
                if (!resultAlgorithm || resultAlgorithm.textContent === '--') {
                    showToast('无数据', '没有可导出的结果数据', 'warning');
                    return;
                }

                // 收集结果数据
                const resultData = {
                    algorithm: resultAlgorithm.textContent,
                    pathLength: resultPathLength ? resultPathLength.textContent : 'N/A',
                    planningTime: resultPlanningTime ? resultPlanningTime.textContent : 'N/A',
                    iterations: resultIterations ? resultIterations.textContent : 'N/A',
                    nodes: resultNodes ? resultNodes.textContent : 'N/A',
                    success: resultSuccess ? resultSuccess.textContent : 'N/A',
                    parameters: {}
                };

                // 添加详细参数
                if (resultDetailsTable) {
                    const rows = resultDetailsTable.querySelectorAll('tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length === 2) {
                            resultData.parameters[cells[0].textContent] = cells[1].textContent;
                        }
                    });
                }

                // 创建JSON文件
                const jsonString = JSON.stringify(resultData, null, 2);
                const blob = new Blob([jsonString], { type: 'application/json' });
                const url = URL.createObjectURL(blob);

                // 创建下载链接
                const downloadLink = document.createElement('a');
                downloadLink.href = url;
                downloadLink.download = `RRT_${algorithmSelect ? algorithmSelect.value : 'BaseRRT'}_Results_${new Date().toISOString().slice(0, 10)}.json`;
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);

                // 释放URL对象
                URL.revokeObjectURL(url);

                showToast('导出成功', '结果数据已成功导出为JSON文件');
            } catch (error) {
                console.error('导出数据失败:', error);
                showToast('导出失败', '无法导出结果数据', 'error');
            }
        });
    }

    // 更新结果显示
    function updateResultDisplay(data) {
        if (!data || !data.details) return;

        const details = data.details;

        try {
            // 准备动画效果
            const resultElements = [];
            if (resultAlgorithm) resultElements.push(resultAlgorithm);
            if (resultPathLength) resultElements.push(resultPathLength);
            if (resultPlanningTime) resultElements.push(resultPlanningTime);
            if (resultIterations) resultElements.push(resultIterations);
            if (resultNodes) resultElements.push(resultNodes);
            if (resultSuccess) resultElements.push(resultSuccess);

            // 清除旧内容
            resultElements.forEach(el => {
                if (el) {
                    el.textContent = '';
                    el.classList.add('highlight');
                }
            });

            if (resultDetailsTable) {
                resultDetailsTable.innerHTML = '';
            }

            // 添加延迟显示新内容，创建动画效果
            setTimeout(() => {
                // 更新摘要信息
                if (resultAlgorithm) resultAlgorithm.textContent = details.name || (algorithmSelect ? algorithmSelect.value : 'BaseRRT');
                if (resultPathLength) resultPathLength.textContent = data.success ? formatNumber(details.path_length) : 'N/A';
                if (resultPlanningTime) resultPlanningTime.textContent = details.planning_time ? `${formatNumber(details.planning_time)} 秒` : 'N/A';
                if (resultIterations) resultIterations.textContent = details.iterations || 'N/A';
                if (resultNodes) resultNodes.textContent = details.nodes || 'N/A';

                if (resultSuccess) {
                    resultSuccess.textContent = data.success ? '是' : '否';
                    // 添加颜色指示
                    resultSuccess.className = data.success ? 'highlight text-success' : 'highlight text-danger';
                }

                // 填充详细信息表格
                if (resultDetailsTable) {
                    for (const [key, value] of Object.entries(details)) {
                        // 跳过已在摘要中显示的字段
                        if (['name', 'path_length', 'planning_time', 'iterations', 'nodes', 'success'].includes(key)) {
                            continue;
                        }

                        // 跳过复杂对象
                        if (typeof value === 'object') continue;

                        const row = document.createElement('tr');
                        row.classList.add('fade-in');

                        const paramCell = document.createElement('td');
                        paramCell.textContent = formatParameterName(key);
                        row.appendChild(paramCell);

                        const valueCell = document.createElement('td');
                        valueCell.textContent = formatValue(value);
                        row.appendChild(valueCell);

                        resultDetailsTable.appendChild(row);

                        // 添加延迟以创建顺序出现的效果
                        setTimeout(() => {
                            row.classList.add('show');
                        }, 100 + resultDetailsTable.children.length * 50);
                    }
                }

                // 移除高亮效果
                setTimeout(() => {
                    resultElements.forEach(el => {
                        if (el) el.classList.remove('highlight');
                    });
                }, 300);
            }, 300);
        } catch (error) {
            console.error('更新结果显示时出错:', error);
            showToast('显示结果失败', '无法显示规划结果', 'error');
        }
    }

    // 清除结果显示
    function clearResultDisplay() {
        try {
            if (resultAlgorithm) resultAlgorithm.textContent = '--';
            if (resultPathLength) resultPathLength.textContent = '--';
            if (resultPlanningTime) resultPlanningTime.textContent = '--';
            if (resultIterations) resultIterations.textContent = '--';
            if (resultNodes) resultNodes.textContent = '--';

            if (resultSuccess) {
                resultSuccess.textContent = '--';
                resultSuccess.className = ''; // 移除颜色类
            }

            if (resultDetailsTable) {
                resultDetailsTable.innerHTML = '';
            }
        } catch (error) {
            console.error('清除结果显示时出错:', error);
        }
    }

    // 格式化参数名称
    function formatParameterName(name) {
        return name
            .replace(/_/g, ' ')
            .replace(/\b\w/g, letter => letter.toUpperCase());
    }

    // 格式化数值
    function formatNumber(value) {
        if (typeof value === 'number') {
            return value.toFixed(2);
        }
        return value;
    }

    // 格式化值
    function formatValue(value) {
        if (typeof value === 'number') {
            return formatNumber(value);
        } else if (typeof value === 'boolean') {
            return value ? '是' : '否';
        } else if (Array.isArray(value)) {
            return `[${value.map(formatValue).join(', ')}]`;
        }
        return String(value);
    }

    // 使元素显示闪烁效果
    function pulseElement(element) {
        if (!element) return;
        try {
            element.classList.add('pulse');
            setTimeout(() => {
                element.classList.remove('pulse');
            }, 1000);
        } catch (error) {
            console.warn('Unable to add pulse effect:', error);
        }
    }

    // 显示淡入效果
    function fadeIn(element) {
        if (!element) return;
        try {
            element.style.opacity = '0';
            element.style.transition = 'opacity 0.3s ease';
            setTimeout(() => {
                element.style.opacity = '1';
            }, 10);
        } catch (error) {
            console.warn('Unable to add fade-in effect:', error);
            // 确保元素可见，即使动画失败
            if (element) element.style.opacity = '1';
        }
    }

    // 显示淡出效果
    function fadeOut(element, callback) {
        if (!element) return;
        try {
            element.style.opacity = '1';
            element.style.transition = 'opacity 0.3s ease';
            setTimeout(() => {
                element.style.opacity = '0';
                setTimeout(() => {
                    if (callback) callback();
                }, 300);
            }, 10);
        } catch (error) {
            console.warn('Unable to add fade-out effect:', error);
            // 仍然执行回调，即使动画失败
            if (callback) callback();
        }
    }

    // 显示提示框
    function showToast(title, message, type = 'info') {
        try {
            // 创建提示框元素
            const toast = document.createElement('div');
            toast.className = `toast-notification toast-${type}`;

            // 添加图标
            let icon = '';
            switch(type) {
                case 'success':
                    icon = '<i class="fas fa-check-circle"></i>';
                    break;
                case 'error':
                    icon = '<i class="fas fa-exclamation-circle"></i>';
                    break;
                case 'warning':
                    icon = '<i class="fas fa-exclamation-triangle"></i>';
                    break;
                default:
                    icon = '<i class="fas fa-info-circle"></i>';
            }

            // 设置内容
            toast.innerHTML = `
                <div class="toast-header">
                    ${icon}
                    <strong>${title}</strong>
                    <button type="button" class="toast-close">&times;</button>
                </div>
                <div class="toast-body">${message}</div>
            `;

            // 添加到DOM
            document.body.appendChild(toast);

            // 添加关闭按钮事件
            const closeBtn = toast.querySelector('.toast-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    toast.classList.add('toast-hiding');
                    setTimeout(() => {
                        if (document.body.contains(toast)) {
                            document.body.removeChild(toast);
                        }
                    }, 300);
                });
            }

            // 显示提示框
            setTimeout(() => {
                toast.classList.add('toast-visible');
            }, 10);

            // 自动关闭
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    toast.classList.add('toast-hiding');
                    setTimeout(() => {
                        if (document.body.contains(toast)) {
                            document.body.removeChild(toast);
                        }
                    }, 300);
                }
            }, 5000);
        } catch (error) {
            console.error('显示提示框失败:', error);
            // 降级到简单的alert，如果Toast失败
            if (type === 'error') {
                alert(`错误: ${title}\n${message}`);
            } else if (type === 'warning') {
                alert(`警告: ${title}\n${message}`);
            }
        }
    }

    // 显示错误消息
    function showError(message) {
        console.error(message);
        showToast('错误', message, 'error');
    }

    // 显示警告消息
    function showWarning(message) {
        console.warn(message);
        showToast('警告', message, 'warning');
    }

    // 显示信息消息
    function showInfo(message) {
        console.log(message);
        showToast('信息', message, 'info');
    }

    // 显示欢迎提示
    function showWelcomeToast() {
        showToast(
            '欢迎使用RRT可视化工具',
            '这是一个用于演示不同RRT算法的工具。开始使用前，请设置起点和终点，然后选择算法并设置参数。'
        );
    }

    // 初始化工具提示
    function initializeTooltips() {
        try {
            // 添加CSS
            const style = document.createElement('style');
            style.textContent = `
                .toast-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    min-width: 300px;
                    max-width: 400px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    z-index: 9999;
                    opacity: 0;
                    transform: translateY(-20px);
                    transition: opacity 0.3s ease, transform 0.3s ease;
                    overflow: hidden;
                }

                .toast-visible {
                    opacity: 1;
                    transform: translateY(0);
                }

                .toast-hiding {
                    opacity: 0;
                    transform: translateY(-20px);
                }

                .toast-header {
                    display: flex;
                    align-items: center;
                    padding: 10px 15px;
                    background-color: #f8f9fa;
                    border-bottom: 1px solid rgba(0,0,0,0.05);
                }

                .toast-header i {
                    margin-right: 10px;
                    font-size: 1.2rem;
                }

                .toast-header strong {
                    flex-grow: 1;
                    font-size: 1rem;
                }

                .toast-close {
                    background: none;
                    border: none;
                    font-size: 1.2rem;
                    cursor: pointer;
                    opacity: 0.5;
                    transition: opacity 0.2s ease;
                }

                .toast-close:hover {
                    opacity: 1;
                }

                .toast-body {
                    padding: 15px;
                    font-size: 0.9rem;
                    color: #6c757d;
                }

                .toast-info i { color: #0d6efd; }
                .toast-success i { color: #198754; }
                .toast-warning i { color: #ffc107; }
                .toast-error i { color: #dc3545; }

                /* 添加输入元素脉冲效果 */
                .pulse {
                    animation: pulse-animation 1s ease;
                }

                @keyframes pulse-animation {
                    0% { box-shadow: 0 0 0 0 rgba(13, 110, 253, 0.7); }
                    50% { box-shadow: 0 0 0 10px rgba(13, 110, 253, 0); }
                    100% { box-shadow: 0 0 0 0 rgba(13, 110, 253, 0); }
                }

                /* 高亮动画 */
                .highlight {
                    transition: color 0.3s ease;
                    color: #0d6efd !important;
                }

                /* 表格渐入效果 */
                .fade-in {
                    opacity: 0;
                    transform: translateY(10px);
                    transition: opacity 0.3s ease, transform 0.3s ease;
                }

                .fade-in.show {
                    opacity: 1;
                    transform: translateY(0);
                }

                /* 按钮波纹效果 */
                .btn {
                    position: relative;
                    overflow: hidden;
                }

                .ripple {
                    position: absolute;
                    border-radius: 50%;
                    background-color: rgba(255, 255, 255, 0.4);
                    transform: scale(0);
                    animation: ripple 0.6s linear;
                }

                @keyframes ripple {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }

                /* 兼容性样式 */
                .text-success { color: #198754 !important; }
                .text-danger { color: #dc3545 !important; }
                .text-primary { color: #0d6efd !important; }

                /* 备用图标 */
                .fallback-icon::before {
                    display: inline-block;
                    width: 1em;
                    text-align: center;
                    margin-right: 0.25em;
                }
                .fallback-icon.success::before { content: "✓"; color: #198754; }
                .fallback-icon.error::before { content: "⚠"; color: #dc3545; }
                .fallback-icon.warning::before { content: "!"; color: #ffc107; }
                .fallback-icon.info::before { content: "i"; color: #0d6efd; }
            `;
            document.head.appendChild(style);

            // 检查Font Awesome是否加载
            setTimeout(() => {
                const fontAwesomeLoaded = Array.from(document.styleSheets).some(sheet =>
                    sheet.href && sheet.href.includes('font-awesome')
                );

                if (!fontAwesomeLoaded) {
                    console.warn('Font Awesome not loaded, using backup icons');

                    // 添加备用图标CSS
                    const fallbackStyle = document.createElement('style');
                    fallbackStyle.textContent = `
                        .fas.fa-cogs::before { content: "⚙"; }
                        .fas.fa-map::before { content: "🗺"; }
                        .fas.fa-code-branch::before { content: "Y"; }
                        .fas.fa-arrows-alt-h::before { content: "↔"; }
                        .fas.fa-redo::before { content: "↻"; }
                        .fas.fa-bullseye::before { content: "◎"; }
                        .fas.fa-search::before { content: "🔍"; }
                        .fas.fa-play-circle::before { content: "▶"; }
                        .fas.fa-flag-checkered::before { content: "🏁"; }
                        .fas.fa-crosshairs::before { content: "⊕"; }
                        .fas.fa-ban::before { content: "⛔"; }
                        .fas.fa-square::before { content: "■"; }
                        .fas.fa-circle::before { content: "●"; }
                        .fas.fa-plus::before { content: "+"; }
                        .fas.fa-trash-alt::before { content: "🗑"; }
                        .fas.fa-play::before { content: "▶"; }
                        .fas.fa-download::before { content: "↓"; }
                        .fas.fa-file-export::before { content: "📤"; }
                        .fas.fa-check-circle::before { content: "✓"; }
                        .fas.fa-exclamation-circle::before { content: "⚠"; }
                        .fas.fa-exclamation-triangle::before { content: "⚠"; }
                        .fas.fa-info-circle::before { content: "i"; }
                    `;
                    document.head.appendChild(fallbackStyle);
                }
            }, 2000);
        } catch (error) {
            console.error('初始化工具提示失败:', error);
        }
    }

    // 兼容性检查
    function checkBrowserCompatibility() {
        const issues = [];

        // 检查Canvas支持
        if (!document.createElement('canvas').getContext) {
            issues.push('您的浏览器不支持Canvas，可视化功能将不可用');
        }

        // 检查Fetch API支持
        if (typeof fetch === 'undefined') {
            issues.push('您的浏览器不支持Fetch API，请使用现代浏览器');
        }

        // 显示兼容性问题
        if (issues.length > 0) {
            showError('兼容性问题：' + issues.join('; '));
        }
    }

    // 执行兼容性检查
    checkBrowserCompatibility();

    // 初始化设置
    // 更新输入框以匹配可视化器的默认值
    setTimeout(() => {
        console.log('Initializing UI to match visualizer defaults');

        if (!visualizer) {
            console.warn('Visualizer not available for initialization');
            return;
        }

        // 获取可视化器的当前状态
        const { start, goal } = visualizer.state;

        // 如果有默认起点，更新输入框
        if (start && startXInput && startYInput) {
            startXInput.value = Math.floor(start.x);
            startYInput.value = Math.floor(start.y);
            console.log('Updated start input fields to:', start.x, start.y);
        }

        // 如果有默认终点，更新输入框
        if (goal && goalXInput && goalYInput) {
            goalXInput.value = Math.floor(goal.x);
            goalYInput.value = Math.floor(goal.y);
            console.log('Updated goal input fields to:', goal.x, goal.y);
        }

        // 强制渲染确保显示
        visualizer.render();
    }, 500); // 延迟以确保组件已完全加载
    const loadedConfig = getLoadedConfig();
    if (loadedConfig) {
        console.log('正在加载配置:', loadedConfig.name);

        try {
            // 显示加载动画
            if (loadingOverlay) {
                loadingOverlay.classList.remove('d-none');
            }

            const configData = loadedConfig.data;

            // 1. 加载算法设置
            if (configData.algorithm && algorithmSelect) {
                algorithmSelect.value = configData.algorithm;
                updateAlgorithmParameters(); // 更新相关参数显示/隐藏
            }

            // 2. 加载参数
            if (configData.parameters) {
                const params = configData.parameters;
                if (stepSizeSlider && params.stepSize) {
                    stepSizeSlider.value = params.stepSize;
                    stepSizeValue.textContent = params.stepSize;
                }

                if (maxIterationsSlider && params.maxIterations) {
                    maxIterationsSlider.value = params.maxIterations;
                    maxIterationsValue.textContent = params.maxIterations;
                }

                if (goalSampleRateSlider && params.goalSampleRate) {
                    goalSampleRateSlider.value = params.goalSampleRate;
                    goalSampleRateValue.textContent = params.goalSampleRate;
                }

                if (searchRadiusSlider && params.searchRadius) {
                    searchRadiusSlider.value = params.searchRadius;
                    searchRadiusValue.textContent = params.searchRadius;
                }
            }

            // 3. 加载环境设置
            if (configData.environment) {
                const env = configData.environment;

                // 设置起点和终点
                if (env.start && env.start.length === 2) {
                    if (startXInput) startXInput.value = env.start[0];
                    if (startYInput) startYInput.value = env.start[1];

                    if (visualizer) {
                        visualizer.setStart(env.start[0], env.start[1]);
                    }
                }

                if (env.goal && env.goal.length === 2) {
                    if (goalXInput) goalXInput.value = env.goal[0];
                    if (goalYInput) goalYInput.value = env.goal[1];

                    if (visualizer) {
                        visualizer.setGoal(env.goal[0], env.goal[1]);
                    }
                }

                // 加载障碍物
                if (env.obstacles && env.obstacles.length > 0 && visualizer) {
                    visualizer.clearObstacles();

                    for (const obstacle of env.obstacles) {
                        if (obstacle.type === 'rectangle') {
                            visualizer.addRectangleObstacle(
                                obstacle.x, obstacle.y,
                                obstacle.width, obstacle.height
                            );
                        } else if (obstacle.type === 'circle') {
                            visualizer.addCircleObstacle(
                                obstacle.centerX, obstacle.centerY,
                                obstacle.radius
                            );
                        }
                    }
                }
            }

            // 4. 如果有结果，可以显示结果（可选）
            if (configData.result && configData.result.success !== undefined) {
                // 更新结果面板 - 简化版，只显示基本数据
                const result = configData.result;

                if (resultAlgorithm) resultAlgorithm.textContent = configData.algorithm || 'N/A';
                if (resultPathLength) resultPathLength.textContent = result.path_length || 'N/A';
                if (resultPlanningTime) resultPlanningTime.textContent = result.planning_time || 'N/A';
                if (resultIterations) resultIterations.textContent = result.iterations || 'N/A';
                if (resultNodes) resultNodes.textContent = result.nodes || 'N/A';

                if (resultSuccess) {
                    resultSuccess.textContent = result.success ? '是' : '否';
                    resultSuccess.className = result.success ? 'text-success' : 'text-danger';
                }
            }

            // 隐藏加载动画
            if (loadingOverlay) {
                loadingOverlay.classList.add('d-none');
            }

            // 显示加载成功消息
            showToast('配置已加载', `已成功加载配置"${loadedConfig.name}"`, 'success');

            // 清除会话中的配置数据以避免重复加载
            clearLoadedConfig();

        } catch (error) {
            console.error('加载配置时出错:', error);

            // 隐藏加载动画
            if (loadingOverlay) {
                loadingOverlay.classList.add('d-none');
            }

            showToast('加载失败', '无法加载配置，配置数据可能不兼容', 'error');
        }
    }

    // 处理保存配置按钮
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', function() {
            // 显示保存配置模态框
            const modal = new bootstrap.Modal(document.getElementById('saveConfigModal'));
            modal.show();
        });
    }

    // 保存配置表单提交
    const saveConfigForm = document.getElementById('saveConfigForm');
    if (saveConfigForm) {
        saveConfigForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const configName = document.getElementById('configName').value.trim();
            if (!configName) {
                showToast('错误', '请输入配置名称', 'error');
                return;
            }

            // 构建配置数据对象
            const configData = {
                algorithm: algorithmSelect ? algorithmSelect.value : 'BaseRRT',
                parameters: {
                    stepSize: stepSizeSlider ? Number(stepSizeSlider.value) : 20,
                    maxIterations: maxIterationsSlider ? Number(maxIterationsSlider.value) : 1000,
                    goalSampleRate: goalSampleRateSlider ? Number(goalSampleRateSlider.value) : 0.05,
                    searchRadius: searchRadiusSlider ? Number(searchRadiusSlider.value) : 50
                },
                environment: {
                    start: [startXInput ? Number(startXInput.value) : 50, startYInput ? Number(startYInput.value) : 50],
                    goal: [goalXInput ? Number(goalXInput.value) : 750, goalYInput ? Number(goalYInput.value) : 550],
                    obstacles: visualizer && visualizer.state ? visualizer.state.obstacles : []
                }
            };

            // 获取结果数据（如果有）
            if (resultSuccess && resultSuccess.textContent !== '--') {
                configData.result = {
                    success: resultSuccess.textContent === '是',
                    path_length: resultPathLength ? resultPathLength.textContent : 'N/A',
                    planning_time: resultPlanningTime ? resultPlanningTime.textContent : 'N/A',
                    iterations: resultIterations ? resultIterations.textContent : 'N/A',
                    nodes: resultNodes ? resultNodes.textContent : 'N/A'
                };
            }

            // 显示加载动画
            if (loadingOverlay) {
                loadingOverlay.classList.remove('d-none');
            }

            // 发送保存请求
            fetch('/save_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({
                    config_name: configName,
                    config_data: configData
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('保存配置失败');
                }
                return response.json();
            })
            .then(data => {
                // 隐藏加载动画
                if (loadingOverlay) {
                    loadingOverlay.classList.add('d-none');
                }

                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('saveConfigModal'));
                modal.hide();

                // 显示成功消息
                showToast('配置已保存', `配置"${configName}"已成功保存`, 'success');

                // 清空表单
                document.getElementById('configName').value = '';
            })
            .catch(error => {
                // 隐藏加载动画
                if (loadingOverlay) {
                    loadingOverlay.classList.add('d-none');
                }

                console.error('保存配置时出错:', error);
                showToast('保存失败', error.message, 'error');
            });
        });
    }
});

// 辅助函数：从会话存储中获取预加载的配置
function getLoadedConfig() {
    const configJson = sessionStorage.getItem('loaded_config');
    if (configJson) {
        try {
            return JSON.parse(configJson);
        } catch (e) {
            console.error('解析预加载配置时出错:', e);
            return null;
        }
    }
    return null;
}

// 清除会话中的预加载配置
function clearLoadedConfig() {
    sessionStorage.removeItem('loaded_config');
}

});

// 为老浏览器添加兼容性垫片
if (!Object.entries) {
    Object.entries = function(obj) {
        var ownProps = Object.keys(obj),
            i = ownProps.length,
            resArray = new Array(i);
        while (i--) {
            resArray[i] = [ownProps[i], obj[ownProps[i]]];
        }
        return resArray;
    };
}
// 初始化会话存储 - 用于配置加载
document.addEventListener('DOMContentLoaded', function() {
    // 检查后端是否设置了loaded_config
    const configScript = document.getElementById('loaded_config_data');
    if (configScript && configScript.textContent) {
        try {
            const config = JSON.parse(configScript.textContent);
            sessionStorage.setItem('loaded_config', JSON.stringify(config));
        } catch (e) {
            console.error('解析配置数据时出错:', e);
        }
    }
});
// 错误处理
window.addEventListener('error', function(e) {
    console.error('Global error:', e.message);

    // 创建简单错误提示
    try {
        const alert = document.createElement('div');
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.left = '50%';
        alert.style.transform = 'translateX(-50%)';
        alert.style.padding = '10px 20px';
        alert.style.backgroundColor = '#f44336';
        alert.style.color = 'white';
        alert.style.borderRadius = '4px';
        alert.style.zIndex = '9999';
        alert.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        alert.style.fontFamily = 'Arial, sans-serif';

        const errorMsg = e.message || '应用程序出现错误';
        alert.textContent = '错误：' + errorMsg;

        document.body.appendChild(alert);

        setTimeout(() => {
            if (document.body.contains(alert)) {
                document.body.removeChild(alert);
            }
        }, 5000);
    } catch (alertError) {
        // 如果连创建错误提示都失败了，回退到console
        console.error('无法显示错误提示:', alertError);
    }
});