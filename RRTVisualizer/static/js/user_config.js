/**
 * user_config.js - 用户配置管理JavaScript功能
 * 处理配置的保存、加载和删除操作
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('User config module initialized');

    // 保存当前配置
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
                alert('请输入配置名称');
                return;
            }

            // 获取当前算法配置
            const algorithmSelect = document.getElementById('algorithmSelect');
            const stepSize = document.getElementById('stepSize');
            const maxIterations = document.getElementById('maxIterations');
            const goalSampleRate = document.getElementById('goalSampleRate');
            const searchRadius = document.getElementById('searchRadius');

            // 获取环境配置
            const startX = document.getElementById('startX');
            const startY = document.getElementById('startY');
            const goalX = document.getElementById('goalX');
            const goalY = document.getElementById('goalY');

            // 获取障碍物数据
            let obstacles = [];
            if (window.visualizer && window.visualizer.state && window.visualizer.state.obstacles) {
                obstacles = window.visualizer.state.obstacles;
            }

            // 获取结果数据
            let result = null;
            const resultSuccess = document.getElementById('resultSuccess');
            if (resultSuccess && resultSuccess.textContent !== '--') {
                result = {
                    success: resultSuccess.textContent === '是',
                    path_length: document.getElementById('resultPathLength')?.textContent || 'N/A',
                    planning_time: document.getElementById('resultPlanningTime')?.textContent || 'N/A',
                    iterations: document.getElementById('resultIterations')?.textContent || 'N/A',
                    nodes: document.getElementById('resultNodes')?.textContent || 'N/A'
                };
            }

            // 构建配置对象
            const configData = {
                algorithm: algorithmSelect ? algorithmSelect.value : 'BaseRRT',
                parameters: {
                    stepSize: stepSize ? Number(stepSize.value) : 20,
                    maxIterations: maxIterations ? Number(maxIterations.value) : 1000,
                    goalSampleRate: goalSampleRate ? Number(goalSampleRate.value) : 0.05,
                    searchRadius: searchRadius ? Number(searchRadius.value) : 50
                },
                environment: {
                    start: [startX ? Number(startX.value) : 50, startY ? Number(startY.value) : 50],
                    goal: [goalX ? Number(goalX.value) : 750, goalY ? Number(goalY.value) : 550],
                    obstacles: obstacles
                },
                result: result
            };

            // 显示加载动画
            toggleLoadingOverlay(true);

            // 发送保存请求
            fetch('/save_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    config_name: configName,
                    config_data: configData
                })
            })
            .then(response => {
                toggleLoadingOverlay(false);

                if (!response.ok) {
                    throw new Error('保存配置失败');
                }
                return response.json();
            })
            .then(data => {
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('saveConfigModal'));
                modal.hide();

                // 显示成功消息
                showToast('配置已保存', `配置"${configName}"已成功保存`, 'success');

                // 清空表单
                document.getElementById('configName').value = '';
            })
            .catch(error => {
                console.error('保存配置时出错:', error);
                showToast('保存失败', error.message, 'error');
            });
        });
    }

    // 加载我的配置下拉菜单
    const loadConfigDropdown = document.getElementById('loadConfigDropdown');
    if (loadConfigDropdown) {
        loadConfigDropdown.addEventListener('click', function() {
            // 获取用户配置列表
            fetch('/get_user_configs')
                .then(response => response.json())
                .then(data => {
                    const dropdown = document.getElementById('userConfigsDropdown');
                    dropdown.innerHTML = ''; // 清除现有项目

                    if (Object.keys(data).length === 0) {
                        // 没有保存的配置
                        const emptyItem = document.createElement('li');
                        emptyItem.className = 'dropdown-item disabled';
                        emptyItem.textContent = '没有保存的配置';
                        dropdown.appendChild(emptyItem);
                    } else {
                        // 添加配置项目
                        for (const [name, config] of Object.entries(data)) {
                            const item = document.createElement('li');
                            const link = document.createElement('a');
                            link.className = 'dropdown-item';
                            link.href = `/load_config/${encodeURIComponent(name)}`;
                            link.textContent = name;

                            // 添加配置日期作为小标签
                            if (config.created_at) {
                                const badge = document.createElement('span');
                                badge.className = 'badge bg-secondary float-end';
                                const date = new Date(config.created_at);
                                badge.textContent = `${date.toLocaleDateString()}`;
                                link.appendChild(badge);
                            }

                            item.appendChild(link);
                            dropdown.appendChild(item);
                        }
                    }
                })
                .catch(error => {
                    console.error('获取配置列表时出错:', error);
                    showToast('加载失败', '无法获取配置列表', 'error');
                });
        });
    }

    // 获取CSRF令牌
    function getCsrfToken() {
        return document.querySelector('input[name="csrf_token"]')?.value;
    }

    // 显示/隐藏加载动画
    function toggleLoadingOverlay(show) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            if (show) {
                loadingOverlay.classList.remove('d-none');
            } else {
                loadingOverlay.classList.add('d-none');
            }
        }
    }

    // 显示提示框
    function showToast(title, message, type = 'info') {
        // 查找或创建提示框容器
        let toastsContainer = document.querySelector('.toast-container');
        if (!toastsContainer) {
            toastsContainer = document.createElement('div');
            toastsContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastsContainer);
        }

        // 创建新的提示框
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header ${type === 'error' ? 'bg-danger text-white' : type === 'success' ? 'bg-success text-white' : ''}">
                    <strong class="me-auto">${title}</strong>
                    <small>刚刚</small>
                    <button type="button" class="btn-close ${type === 'error' || type === 'success' ? 'btn-close-white' : ''}" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastsContainer.insertAdjacentHTML('beforeend', toastHTML);

        // 初始化并显示提示框
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 5000
        });
        toast.show();

        // 自动移除DOM元素
        toastElement.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    }
});