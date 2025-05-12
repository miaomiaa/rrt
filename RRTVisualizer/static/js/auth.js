/**
 * auth.js - 用户认证相关JavaScript功能
 * 处理登录、注册表单验证和交互
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Auth module initialized');

    // 登录表单验证
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;

            if (username === '' || password === '') {
                event.preventDefault();
                showAlert('请填写所有必填字段', 'danger');
                return;
            }
        });
    }

    // 注册表单验证
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const username = document.getElementById('username').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            const agreement = document.getElementById('agreement');

            // 检查必填字段
            if (username === '' || email === '' || password === '' || confirmPassword === '') {
                event.preventDefault();
                showAlert('请填写所有必填字段', 'danger');
                return;
            }

            // 用户名格式验证
            if (!/^[a-zA-Z0-9_]{3,20}$/.test(username)) {
                event.preventDefault();
                showAlert('用户名必须是3-20个字符，只能包含字母、数字和下划线', 'danger');
                return;
            }

            // 邮箱格式验证
            if (!/^[\w-]+(\.[\w-]+)*@([\w-]+\.)+[a-zA-Z]{2,7}$/.test(email)) {
                event.preventDefault();
                showAlert('请输入有效的电子邮箱地址', 'danger');
                return;
            }

            // 密码长度验证
            if (password.length < 8) {
                event.preventDefault();
                showAlert('密码必须至少8个字符', 'danger');
                return;
            }

            // 密码复杂度验证
            if (!/\d/.test(password) || !/[a-zA-Z]/.test(password)) {
                event.preventDefault();
                showAlert('密码必须包含至少一个字母和一个数字', 'danger');
                return;
            }

            // 密码匹配验证
            if (password !== confirmPassword) {
                event.preventDefault();
                showAlert('两次输入的密码不匹配', 'danger');
                return;
            }

            // 协议同意验证
            if (agreement && !agreement.checked) {
                event.preventDefault();
                showAlert('您必须同意服务条款和隐私政策', 'danger');
                return;
            }
        });
    }

    // 密码更改表单验证
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', function(event) {
            const currentPassword = document.getElementById('current_password').value;
            const newPassword = document.getElementById('new_password').value;
            const confirmPassword = document.getElementById('confirm_password').value;

            // 检查必填字段
            if (currentPassword === '' || newPassword === '' || confirmPassword === '') {
                event.preventDefault();
                showAlert('请填写所有必填字段', 'danger');
                return;
            }

            // 密码长度验证
            if (newPassword.length < 8) {
                event.preventDefault();
                showAlert('新密码必须至少8个字符', 'danger');
                return;
            }

            // 密码复杂度验证
            if (!/\d/.test(newPassword) || !/[a-zA-Z]/.test(newPassword)) {
                event.preventDefault();
                showAlert('新密码必须包含至少一个字母和一个数字', 'danger');
                return;
            }

            // 密码匹配验证
            if (newPassword !== confirmPassword) {
                event.preventDefault();
                showAlert('两次输入的新密码不匹配', 'danger');
                return;
            }

            // 新密码不能与当前密码相同
            if (newPassword === currentPassword) {
                event.preventDefault();
                showAlert('新密码不能与当前密码相同', 'danger');
                return;
            }
        });
    }

    // 显示密码切换
    const togglePasswordBtns = document.querySelectorAll('[id^="togglePassword"]');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target') || 'password';
            const passwordInput = document.getElementById(targetId);
            const icon = this.querySelector('i');

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // 用户名可用性检查
    const usernameField = document.getElementById('username');
    if (usernameField && registerForm) {
        let typingTimer;
        const doneTypingInterval = 500; // 用户停止输入0.5秒后检查

        usernameField.addEventListener('keyup', function() {
            clearTimeout(typingTimer);
            if (usernameField.value.trim() !== '') {
                typingTimer = setTimeout(checkUsernameAvailability, doneTypingInterval);
            }
        });

        function checkUsernameAvailability() {
            const username = usernameField.value.trim();
            if (!/^[a-zA-Z0-9_]{3,20}$/.test(username)) {
                return; // 先不检查可用性，等格式正确再检查
            }

            // 使用Fetch API发送AJAX请求
            fetch('/check_username?username=' + encodeURIComponent(username))
                .then(response => response.json())
                .then(data => {
                    const feedbackElement = document.getElementById('usernameFeedback');
                    if (!feedbackElement) {
                        // 创建反馈元素
                        const newFeedback = document.createElement('div');
                        newFeedback.id = 'usernameFeedback';
                        newFeedback.className = data.available ? 'valid-feedback' : 'invalid-feedback';
                        newFeedback.style.display = 'block';
                        newFeedback.textContent = data.available ? '用户名可用' : '用户名已被使用';
                        usernameField.parentNode.appendChild(newFeedback);
                    } else {
                        // 更新现有反馈元素
                        feedbackElement.className = data.available ? 'valid-feedback' : 'invalid-feedback';
                        feedbackElement.textContent = data.available ? '用户名可用' : '用户名已被使用';
                        feedbackElement.style.display = 'block';
                    }

                    // 设置输入框的有效性状态
                    if (data.available) {
                        usernameField.classList.remove('is-invalid');
                        usernameField.classList.add('is-valid');
                    } else {
                        usernameField.classList.remove('is-valid');
                        usernameField.classList.add('is-invalid');
                    }
                })
                .catch(error => {
                    console.error('检查用户名可用性时出错:', error);
                });
        }
    }

    // 显示自定义警告
    function showAlert(message, type = 'info') {
        const alertsContainer = document.querySelector('.auth-container');
        if (!alertsContainer) return;

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // 在容器的开头插入警告
        alertsContainer.insertBefore(alertDiv, alertsContainer.firstChild);

        // 5秒后自动删除
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }
});