/**
 * RRT可视化器
 * 处理Canvas绘制和算法可视化
 */

class RRTVisualizer {
    constructor(canvasId) {
        // 获取Canvas元素和上下文
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('Canvas元素未找到:', canvasId);
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        if (!this.ctx) {
            console.error('无法获取Canvas上下文');
            return;
        }

        // 确保Canvas尺寸正确设置
        this.updateCanvasSize();

        // 配置
        this.config = {
            width: this.canvas.width,
            height: this.canvas.height,
            gridSize: 50,
            showGrid: true,
            animation: {
                enabled: true,
                speed: 1, // 动画速度，值越大越快
                nodeDelay: 10, // 节点显示延迟（毫秒）
                pathDelay: 20 // 路径显示延迟（毫秒）
            },
            colors: {
                background: '#ffffff',
                grid: {
                    minor: 'rgba(220, 220, 225, 0.4)',
                    major: 'rgba(180, 180, 190, 0.6)',
                },
                border: '#505050',
                start: {
                    fill: '#4caf50',  // 更鲜艳的绿色
                    stroke: '#2e7d32'
                },
                goal: {
                    fill: '#f44336',  // 更鲜艳的红色
                    stroke: '#c62828'
                },
                tree: {
                    node: '#2196f3',  // 蓝色
                    edge: 'rgba(33, 150, 243, 0.6)'
                },
                path: '#ff1e1e',
                obstacles: {
                    fill: '#424242',
                    stroke: '#212121',
                    gradient: {
                        start: '#424242',
                        end: '#212121'
                    }
                }
            },
            startRadius: 10,
            goalRadius: 10,
            nodeRadius: 3,
            edgeWidth: 1.5,
            pathWidth: 3.5
        };

        // 状态
        this.state = {
            start: { x: 50, y: 50 }, // 默认起点
            goal: { x: 750, y: 550 }, // 默认终点
            obstacles: [],
            nodes: [],
            edges: [],
            path: [],
            mode: 'none', // 当前交互模式: none, setStart, setGoal, addObstacle
            animationInProgress: false,
            animationFrame: null
        };

        // 动画相关
        this.animationQueue = [];
        this.renderedNodes = [];
        this.renderedEdges = [];
        this.renderedPath = [];

        // 初始化
        this.setupMouseTracking();
        this.setupClickHandlers();

        // 添加窗口大小变化监听器
        window.addEventListener('resize', () => this.updateCanvasSize());

        // 初始渲染
        this.render();

        console.log('Visualizer initialized with dimensions:', this.canvas.width, 'x', this.canvas.height);
    }

    // 更新Canvas尺寸
    updateCanvasSize() {
        const containerWidth = this.canvas.parentElement.clientWidth;

        // 保持宽高比 4:3
        if (this.canvas.width !== containerWidth) {
            this.canvas.width = containerWidth;
            this.canvas.height = Math.floor(containerWidth * 0.75); // 保持 4:3 比例

            if (this.config) {
                this.config.width = this.canvas.width;
                this.config.height = this.canvas.height;
            }

            console.log('Canvas size updated:', this.canvas.width, 'x', this.canvas.height);

            if (this.state && this.state.goal) {
                // 保持终点在右下角区域
                if (this.state.goal.x > this.canvas.width - 50) {
                    this.state.goal.x = this.canvas.width - 50;
                }
                if (this.state.goal.y > this.canvas.height - 50) {
                    this.state.goal.y = this.canvas.height - 50;
                }
            }

            if (this.state) {
                this.render();
            }

            return true;
        }

        return false;
    }

    // 鼠标位置跟踪
    setupMouseTracking() {
        const coordsDisplay = document.getElementById('coordsDisplay');
        if (!coordsDisplay) {
            console.warn('坐标显示元素未找到');
            return;
        }

        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor(e.clientX - rect.left);
            const y = Math.floor(e.clientY - rect.top);

            // 显示坐标
            coordsDisplay.textContent = `X: ${x}, Y: ${y}`;

            // 根据当前模式更改鼠标样式
            if (this.state.mode === 'setStart' || this.state.mode === 'setGoal') {
                this.canvas.style.cursor = 'crosshair';
            } else {
                this.canvas.style.cursor = 'default';
            }
        });

        this.canvas.addEventListener('mouseout', () => {
            coordsDisplay.textContent = '';
            this.canvas.style.cursor = 'default';
        });
    }

    // 设置点击处理
    setupClickHandlers() {
        // 添加Canvas点击事件
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor(e.clientX - rect.left);
            const y = Math.floor(e.clientY - rect.top);

            console.log('Canvas clicked at:', x, y, 'Current mode:', this.state.mode);

            // 根据当前模式处理点击
            if (this.state.mode === 'setStart') {
                this.setStart(x, y);
                this.state.mode = 'none'; // 重置模式
                this.canvas.style.cursor = 'default';
                this.showTooltip('起点已设置', x, y);
            }
            else if (this.state.mode === 'setGoal') {
                this.setGoal(x, y);
                this.state.mode = 'none'; // 重置模式
                this.canvas.style.cursor = 'default';
                this.showTooltip('终点已设置', x, y);
            }
        });
    }

    // 显示工具提示
    showTooltip(text, x, y) {
        // 创建工具提示元素
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        tooltip.style.left = `${x + 10}px`;
        tooltip.style.top = `${y - 30}px`;

        // 添加到DOM
        document.body.appendChild(tooltip);

        // 淡入效果
        tooltip.style.opacity = '0';
        setTimeout(() => {
            tooltip.style.opacity = '1';
            tooltip.style.transition = 'opacity 0.3s ease';
        }, 10);

        // 2秒后淡出并移除
        setTimeout(() => {
            tooltip.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(tooltip);
            }, 300);
        }, 2000);
    }

    // 进入设置起点模式
    enterSetStartMode() {
        this.state.mode = 'setStart';
        console.log('Entered set start mode');
    }

    // 进入设置终点模式
    enterSetGoalMode() {
        this.state.mode = 'setGoal';
        console.log('Entered set goal mode');
    }

    // 清除画布
    clear() {
        if (!this.ctx) return;
        this.ctx.fillStyle = this.config.colors.background;
        this.ctx.fillRect(0, 0, this.config.width, this.config.height);
    }

    // 绘制网格
    drawGrid() {
        if (!this.ctx || !this.config.showGrid) return;

        const { width, height, gridSize } = this.config;
        const { minor, major } = this.config.colors.grid;

        this.ctx.save();

        // 绘制水平网格线
        for (let y = 0; y <= height; y += gridSize) {
            this.ctx.beginPath();

            // 主要网格线（100的倍数）使用不同样式
            if (y % (gridSize * 2) === 0) {
                this.ctx.strokeStyle = major;
                this.ctx.setLineDash([5, 3]);
            } else {
                this.ctx.strokeStyle = minor;
                this.ctx.setLineDash([2, 2]);
            }

            this.ctx.moveTo(0, y);
            this.ctx.lineTo(width, y);
            this.ctx.stroke();
        }

        // 绘制垂直网格线
        for (let x = 0; x <= width; x += gridSize) {
            this.ctx.beginPath();

            // 主要网格线（100的倍数）使用不同样式
            if (x % (gridSize * 2) === 0) {
                this.ctx.strokeStyle = major;
                this.ctx.setLineDash([5, 3]);
            } else {
                this.ctx.strokeStyle = minor;
                this.ctx.setLineDash([2, 2]);
            }

            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, height);
            this.ctx.stroke();
        }

        this.ctx.restore();
    }

    // 绘制边界
    drawBorder() {
        if (!this.ctx) return;
        const { width, height } = this.config;

        this.ctx.save();
        this.ctx.strokeStyle = this.config.colors.border;
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(0, 0, width, height);
        this.ctx.restore();
    }

    // 绘制起点
    drawStart() {
        if (!this.ctx || !this.state.start) {
            console.warn('无法绘制起点：缺少上下文或起点坐标');
            return;
        }

        const { x, y } = this.state.start;
        const { startRadius } = this.config;
        const { fill, stroke } = this.config.colors.start;

        this.ctx.save();

        // 绘制外发光效果
        const glowRadius = startRadius + 5;
        const gradient = this.ctx.createRadialGradient(
            x, y, startRadius * 0.8,
            x, y, glowRadius
        );
        gradient.addColorStop(0, 'rgba(76, 175, 80, 0.6)');
        gradient.addColorStop(1, 'rgba(76, 175, 80, 0)');

        this.ctx.beginPath();
        this.ctx.fillStyle = gradient;
        this.ctx.arc(x, y, glowRadius, 0, Math.PI * 2);
        this.ctx.fill();

        // 绘制起点圆形
        this.ctx.beginPath();
        this.ctx.fillStyle = fill;
        this.ctx.strokeStyle = stroke;
        this.ctx.lineWidth = 2;
        this.ctx.arc(x, y, startRadius, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();

        // 绘制中心小圆
        this.ctx.beginPath();
        this.ctx.fillStyle = '#ffffff';
        this.ctx.arc(x, y, startRadius * 0.5, 0, Math.PI * 2);
        this.ctx.fill();

        this.ctx.restore();
    }

    // 绘制终点
    drawGoal() {
        if (!this.ctx || !this.state.goal) {
            console.warn('无法绘制终点：缺少上下文或终点坐标');
            return;
        }

        const { x, y } = this.state.goal;
        const { goalRadius } = this.config;
        const { fill, stroke } = this.config.colors.goal;

        this.ctx.save();

        // 绘制外发光效果
        const glowRadius = goalRadius + 5;
        const gradient = this.ctx.createRadialGradient(
            x, y, goalRadius * 0.8,
            x, y, glowRadius
        );
        gradient.addColorStop(0, 'rgba(244, 67, 54, 0.6)');
        gradient.addColorStop(1, 'rgba(244, 67, 54, 0)');

        this.ctx.beginPath();
        this.ctx.fillStyle = gradient;
        this.ctx.arc(x, y, glowRadius, 0, Math.PI * 2);
        this.ctx.fill();

        // 绘制目标点旗帜形状
        this.ctx.beginPath();
        this.ctx.fillStyle = fill;
        this.ctx.strokeStyle = stroke;
        this.ctx.lineWidth = 2;
        this.ctx.arc(x, y, goalRadius, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();

        // 绘制中心图案
        this.ctx.beginPath();
        this.ctx.fillStyle = '#ffffff';
        this.ctx.arc(x, y, goalRadius * 0.5, 0, Math.PI * 2);
        this.ctx.fill();

        // 绘制十字形
        this.ctx.beginPath();
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 1.5;
        this.ctx.moveTo(x - goalRadius * 0.3, y);
        this.ctx.lineTo(x + goalRadius * 0.3, y);
        this.ctx.moveTo(x, y - goalRadius * 0.3);
        this.ctx.lineTo(x, y + goalRadius * 0.3);
        this.ctx.stroke();

        this.ctx.restore();
    }

    // 绘制树节点和边
    drawTree() {
        // 如果启用动画且动画正在进行中，则使用动画状态
        if (this.config.animation.enabled && this.state.animationInProgress) {
            this.drawAnimatedEdges();
            this.drawAnimatedNodes();
            return;
        }

        // 否则绘制完整的树
        this.drawEdges();
        this.drawNodes();
    }

    // 绘制节点
    drawNodes() {
        if (!this.ctx) return;
        const { nodes } = this.state;
        const { nodeRadius } = this.config;

        if (!nodes || nodes.length === 0) return;

        this.ctx.save();
        this.ctx.fillStyle = this.config.colors.tree.node;

        for (const node of nodes) {
            if (!node || typeof node.x !== 'number' || typeof node.y !== 'number') {
                continue; // 跳过无效节点
            }

            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, nodeRadius, 0, Math.PI * 2);
            this.ctx.fill();
        }

        this.ctx.restore();
    }

    // 绘制动画状态的节点
    drawAnimatedNodes() {
        if (!this.ctx) return;
        const { nodeRadius } = this.config;

        this.ctx.save();
        this.ctx.fillStyle = this.config.colors.tree.node;

        for (const node of this.renderedNodes) {
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, nodeRadius, 0, Math.PI * 2);
            this.ctx.fill();
        }

        this.ctx.restore();
    }

    // 绘制边
    drawEdges() {
        if (!this.ctx) return;
        const { edges, nodes } = this.state;

        if (!edges || edges.length === 0 || !nodes || nodes.length === 0) return;

        this.ctx.save();
        this.ctx.strokeStyle = this.config.colors.tree.edge;
        this.ctx.lineWidth = this.config.edgeWidth;

        for (const edge of edges) {
            if (!edge || typeof edge.from !== 'number' || typeof edge.to !== 'number') {
                continue; // 跳过无效边
            }

            const from = nodes[edge.from];
            const to = nodes[edge.to];

            if (!from || !to ||
                typeof from.x !== 'number' || typeof from.y !== 'number' ||
                typeof to.x !== 'number' || typeof to.y !== 'number') {
                continue; // 跳过无效点
            }

            this.ctx.beginPath();
            this.ctx.moveTo(from.x, from.y);
            this.ctx.lineTo(to.x, to.y);
            this.ctx.stroke();
        }

        this.ctx.restore();
    }

    // 绘制动画状态的边
    drawAnimatedEdges() {
        if (!this.ctx) return;

        this.ctx.save();
        this.ctx.strokeStyle = this.config.colors.tree.edge;
        this.ctx.lineWidth = this.config.edgeWidth;

        for (const edge of this.renderedEdges) {
            this.ctx.beginPath();
            this.ctx.moveTo(edge.from.x, edge.from.y);
            this.ctx.lineTo(edge.to.x, edge.to.y);
            this.ctx.stroke();
        }

        this.ctx.restore();
    }

    // 绘制路径
    drawPath() {
        if (!this.ctx) return;

        // 如果启用动画且动画正在进行中，则绘制动画状态的路径
        if (this.config.animation.enabled && this.state.animationInProgress) {
            this.drawAnimatedPath();
            return;
        }

        const { path } = this.state;

        if (!path || path.length < 2) return;

        this.ctx.save();
        this.ctx.strokeStyle = this.config.colors.path;
        this.ctx.lineWidth = this.config.pathWidth;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        this.ctx.beginPath();

        let started = false;
        for (const point of path) {
            if (!point || typeof point.x !== 'number' || typeof point.y !== 'number') {
                continue; // 跳过无效点
            }

            if (!started) {
                this.ctx.moveTo(point.x, point.y);
                started = true;
            } else {
                this.ctx.lineTo(point.x, point.y);
            }
        }

        if (started) {
            this.ctx.stroke();
        }

        this.ctx.restore();
    }

    // 绘制动画状态的路径
    drawAnimatedPath() {
        if (!this.ctx || this.renderedPath.length < 2) return;

        this.ctx.save();
        this.ctx.strokeStyle = this.config.colors.path;
        this.ctx.lineWidth = this.config.pathWidth;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        this.ctx.beginPath();
        this.ctx.moveTo(this.renderedPath[0].x, this.renderedPath[0].y);

        for (let i = 1; i < this.renderedPath.length; i++) {
            this.ctx.lineTo(this.renderedPath[i].x, this.renderedPath[i].y);
        }

        this.ctx.stroke();
        this.ctx.restore();
    }

    // 绘制障碍物
    drawObstacles() {
        if (!this.ctx) return;
        const { obstacles } = this.state;

        if (!obstacles || obstacles.length === 0) return;

        const { fill, stroke, gradient } = this.config.colors.obstacles;

        this.ctx.save();

        for (const obstacle of obstacles) {
            if (!obstacle || !obstacle.type) {
                continue; // 跳过无效障碍物
            }

            if (obstacle.type === 'rectangle') {
                if (typeof obstacle.x !== 'number' || typeof obstacle.y !== 'number' ||
                    typeof obstacle.width !== 'number' || typeof obstacle.height !== 'number') {
                    continue; // 跳过无效矩形
                }

                // 矩形障碍物
                // 创建线性渐变
                try {
                    const rectGradient = this.ctx.createLinearGradient(
                        obstacle.x, obstacle.y,
                        obstacle.x + obstacle.width, obstacle.y + obstacle.height
                    );
                    rectGradient.addColorStop(0, gradient.start);
                    rectGradient.addColorStop(1, gradient.end);

                    this.ctx.fillStyle = rectGradient;
                } catch (e) {
                    console.error('创建矩形障碍物渐变失败:', e);
                    this.ctx.fillStyle = fill; // 回退到纯色填充
                }

                this.ctx.strokeStyle = stroke;
                this.ctx.lineWidth = 2;

                // 绘制带圆角的矩形
                const radius = 5; // 圆角半径
                this.ctx.beginPath();
                this.ctx.moveTo(obstacle.x + radius, obstacle.y);
                this.ctx.lineTo(obstacle.x + obstacle.width - radius, obstacle.y);
                this.ctx.quadraticCurveTo(obstacle.x + obstacle.width, obstacle.y, obstacle.x + obstacle.width, obstacle.y + radius);
                this.ctx.lineTo(obstacle.x + obstacle.width, obstacle.y + obstacle.height - radius);
                this.ctx.quadraticCurveTo(obstacle.x + obstacle.width, obstacle.y + obstacle.height, obstacle.x + obstacle.width - radius, obstacle.y + obstacle.height);
                this.ctx.lineTo(obstacle.x + radius, obstacle.y + obstacle.height);
                this.ctx.quadraticCurveTo(obstacle.x, obstacle.y + obstacle.height, obstacle.x, obstacle.y + obstacle.height - radius);
                this.ctx.lineTo(obstacle.x, obstacle.y + radius);
                this.ctx.quadraticCurveTo(obstacle.x, obstacle.y, obstacle.x + radius, obstacle.y);
                this.ctx.closePath();

                this.ctx.fill();
                this.ctx.stroke();

                // 添加纹理效果
                this.ctx.globalAlpha = 0.1;
                this.ctx.strokeStyle = '#ffffff';
                this.ctx.lineWidth = 0.5;

                for (let i = 0; i < obstacle.width; i += 10) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(obstacle.x + i, obstacle.y);
                    this.ctx.lineTo(obstacle.x + i, obstacle.y + obstacle.height);
                    this.ctx.stroke();
                }

                this.ctx.globalAlpha = 1.0;
            }
            else if (obstacle.type === 'circle') {
                if (typeof obstacle.centerX !== 'number' || typeof obstacle.centerY !== 'number' ||
                    typeof obstacle.radius !== 'number') {
                    continue; // 跳过无效圆形
                }

                // 圆形障碍物
                // 创建径向渐变
                try {
                    const circleGradient = this.ctx.createRadialGradient(
                        obstacle.centerX, obstacle.centerY, 0,
                        obstacle.centerX, obstacle.centerY, obstacle.radius
                    );
                    circleGradient.addColorStop(0, gradient.start);
                    circleGradient.addColorStop(1, gradient.end);

                    this.ctx.fillStyle = circleGradient;
                } catch (e) {
                    console.error('创建圆形障碍物渐变失败:', e);
                    this.ctx.fillStyle = fill; // 回退到纯色填充
                }

                this.ctx.strokeStyle = stroke;
                this.ctx.lineWidth = 2;

                this.ctx.beginPath();
                this.ctx.arc(obstacle.centerX, obstacle.centerY, obstacle.radius, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.stroke();

                // 添加纹理效果
                this.ctx.globalAlpha = 0.1;
                this.ctx.strokeStyle = '#ffffff';
                this.ctx.lineWidth = 0.5;

                for (let i = -obstacle.radius; i < obstacle.radius; i += 10) {
                    const chordLength = Math.sqrt(obstacle.radius * obstacle.radius - i * i) * 2;
                    this.ctx.beginPath();
                    this.ctx.moveTo(obstacle.centerX - chordLength / 2, obstacle.centerY + i);
                    this.ctx.lineTo(obstacle.centerX + chordLength / 2, obstacle.centerY + i);
                    this.ctx.stroke();
                }

                this.ctx.globalAlpha = 1.0;
            }
        }

        this.ctx.restore();
    }

    // 渲染所有内容
    render() {
        if (!this.ctx) {
            console.error('无法渲染：Canvas上下文未找到');
            return;
        }

        // 清除上一帧
        this.clear();

        // 绘制背景元素
        this.drawGrid();
        this.drawBorder();
        this.drawObstacles();

        // 绘制树和路径
        this.drawTree();
        this.drawPath();

        // 确保起点和终点被正确绘制
        if (this.state.start) {
            this.drawStart();
        }

        if (this.state.goal) {
            this.drawGoal();
        }
    }

    // 设置起点
    setStart(x, y) {
        if (typeof x !== 'number' || typeof y !== 'number') {
            console.error('设置起点失败：无效的坐标值', x, y);
            return;
        }

        // 确保坐标在Canvas边界内
        x = Math.max(0 + this.config.startRadius, Math.min(this.config.width - this.config.startRadius, x));
        y = Math.max(0 + this.config.startRadius, Math.min(this.config.height - this.config.startRadius, y));

        console.log('设置起点:', x, y);
        this.state.start = { x, y };

        // 更新输入框
        const startXInput = document.getElementById('startX');
        const startYInput = document.getElementById('startY');

        if (startXInput) startXInput.value = Math.floor(x);
        if (startYInput) startYInput.value = Math.floor(y);

        this.render();
    }

    // 设置终点
    setGoal(x, y) {
        if (typeof x !== 'number' || typeof y !== 'number') {
            console.error('设置终点失败：无效的坐标值', x, y);
            return;
        }

        // 确保坐标在Canvas边界内
        x = Math.max(0 + this.config.goalRadius, Math.min(this.config.width - this.config.goalRadius, x));
        y = Math.max(0 + this.config.goalRadius, Math.min(this.config.height - this.config.goalRadius, y));

        console.log('设置终点:', x, y);
        this.state.goal = { x, y };

        // 更新输入框
        const goalXInput = document.getElementById('goalX');
        const goalYInput = document.getElementById('goalY');

        if (goalXInput) goalXInput.value = Math.floor(x);
        if (goalYInput) goalYInput.value = Math.floor(y);

        this.render();
    }

    // 添加矩形障碍物
    addRectangleObstacle(x, y, width, height) {
        if (typeof x !== 'number' || typeof y !== 'number' ||
            typeof width !== 'number' || typeof height !== 'number' ||
            width <= 0 || height <= 0) {
            console.error('添加矩形障碍物失败：无效的参数', x, y, width, height);
            return;
        }

        console.log('添加矩形障碍物:', x, y, width, height);
        this.state.obstacles.push({
            type: 'rectangle',
            x, y, width, height
        });
        this.render();
    }

    // 添加圆形障碍物
    addCircleObstacle(centerX, centerY, radius) {
        if (typeof centerX !== 'number' || typeof centerY !== 'number' ||
            typeof radius !== 'number' || radius <= 0) {
            console.error('添加圆形障碍物失败：无效的参数', centerX, centerY, radius);
            return;
        }

        console.log('添加圆形障碍物:', centerX, centerY, radius);
        this.state.obstacles.push({
            type: 'circle',
            centerX, centerY, radius
        });
        this.render();
    }

    // 清除所有障碍物
    clearObstacles() {
        console.log('清除所有障碍物');
        this.state.obstacles = [];
        this.render();
    }

    // 清除所有内容
    reset() {
        console.log('重置可视化器');

        // 停止任何进行中的动画
        this.stopAnimation();

        // 获取当前Canvas尺寸
        const width = this.canvas.width;
        const height = this.canvas.height;

        // 计算默认起点和终点位置，适应当前Canvas尺寸
        const startX = Math.min(50, width * 0.1);
        const startY = Math.min(50, height * 0.1);
        const goalX = Math.max(width - 50, width * 0.9);
        const goalY = Math.max(height - 50, height * 0.9);

        this.state = {
            start: { x: startX, y: startY },
            goal: { x: goalX, y: goalY },
            obstacles: [],
            nodes: [],
            edges: [],
            path: [],
            mode: 'none',
            animationInProgress: false,
            animationFrame: null
        };

        // 更新输入框
        const startXInput = document.getElementById('startX');
        const startYInput = document.getElementById('startY');
        const goalXInput = document.getElementById('goalX');
        const goalYInput = document.getElementById('goalY');

        if (startXInput) startXInput.value = Math.floor(startX);
        if (startYInput) startYInput.value = Math.floor(startY);
        if (goalXInput) goalXInput.value = Math.floor(goalX);
        if (goalYInput) goalYInput.value = Math.floor(goalY);

        this.render();
    }

    // 清除树和路径，保留环境设置
    clearResult() {
        console.log('清除结果');

        // 停止任何进行中的动画
        this.stopAnimation();

        this.state.nodes = [];
        this.state.edges = [];
        this.state.path = [];
        this.state.animationInProgress = false;
        this.render();
    }

    // 停止动画
    stopAnimation() {
        if (this.state.animationFrame) {
            cancelAnimationFrame(this.state.animationFrame);
            this.state.animationFrame = null;
        }
        this.state.animationInProgress = false;
        this.animationQueue = [];
        this.renderedNodes = [];
        this.renderedEdges = [];
        this.renderedPath = [];
    }

    // 更新RRT结果
    updateResult(result) {
        console.log('更新结果:', result);

        if (!result) return;

        // 清除旧结果
        this.clearResult();

        // 准备数据
        const nodes = result.vertices ? result.vertices.map(v => ({
            x: Number(v[0]),
            y: Number(v[1])
        })) : [];

        const edges = result.edges ? result.edges.map(e => ({
            from: Number(e[0]),
            to: Number(e[1])
        })) : [];

        const path = result.path ? result.path.map(p => ({
            x: Number(p[0]),
            y: Number(p[1])
        })) : [];

        // 更新状态
        this.state.nodes = nodes;
        this.state.edges = edges;
        this.state.path = path;

        // 如果启用动画，则开始动画
        if (this.config.animation.enabled && (edges.length > 0 || path.length > 0)) {
            this.startAnimation(nodes, edges, path);
        } else {
            // 否则直接渲染结果
            this.render();
        }
    }

    // 开始动画
    startAnimation(nodes, edges, path) {
        // 初始化动画状态
        this.state.animationInProgress = true;
        this.renderedNodes = [nodes[0]]; // 起始节点
        this.renderedEdges = [];
        this.renderedPath = [];

        // 构建动画队列
        this.animationQueue = [];

        // 先添加所有边的动画
        for (const edge of edges) {
            this.animationQueue.push({
                type: 'edge',
                edge: {
                    from: nodes[edge.from],
                    to: nodes[edge.to]
                },
                nodeIndex: edge.to
            });
        }

        // 再添加路径的动画
        if (path.length > 0) {
            for (let i = 0; i < path.length - 1; i++) {
                this.animationQueue.push({
                    type: 'path',
                    from: path[i],
                    to: path[i + 1]
                });
            }
        }

        // 开始动画循环
        this.animateStep();
    }

    // 动画步骤
    animateStep() {
        // 如果队列为空或动画被停止，则结束动画
        if (this.animationQueue.length === 0 || !this.state.animationInProgress) {
            this.state.animationInProgress = false;
            return;
        }

        // 取出动画队列中的项目
        const numItemsToProcess = Math.ceil(this.config.animation.speed);
        const items = this.animationQueue.splice(0, numItemsToProcess);

        for (const item of items) {
            if (item.type === 'edge') {
                // 添加边
                this.renderedEdges.push(item.edge);

                // 添加节点（如果尚未添加）
                if (!this.renderedNodes.some(node => node.x === item.edge.to.x && node.y === item.edge.to.y)) {
                    this.renderedNodes.push(item.edge.to);
                }
            } else if (item.type === 'path') {
                // 添加路径段
                if (this.renderedPath.length === 0) {
                    this.renderedPath.push(item.from);
                }
                this.renderedPath.push(item.to);
            }
        }

        // 渲染当前状态
        this.render();

        // 安排下一帧
        this.state.animationFrame = requestAnimationFrame(() => {
            this.animateStep();
        });
    }

    // 导出为图片
    exportToImage() {
        if (!this.canvas) {
            console.error('导出图片失败：Canvas元素未找到');
            return null;
        }

        return this.canvas.toDataURL('image/png');
    }

    // 更新参数
    updateConfig(configUpdates) {
        this.config = { ...this.config, ...configUpdates };
        this.render();
    }
}