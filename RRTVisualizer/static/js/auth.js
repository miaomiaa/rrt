// auth.js - 前端认证相关功能

const Auth = {
    // 检查用户是否已登录
    checkAuth() {
        return fetch('/api/check-auth')
            .then(response => response.json())
            .then(data => data.authenticated)
            .catch(() => false);
    },

    // 获取当前用户信息
    getCurrentUser() {
        return fetch('/api/user-info')
            .then(response => response.json())
            .catch(() => null);
    },

    // 登出
    logout() {
        return fetch('/api/logout', { method: 'POST' })
            .then(() => {
                window.location.href = '/login';
            })
            .catch(error => {
                console.error('登出失败:', error);
                window.location.href = '/login';
            });
    },

    // 初始化认证状态
    async init() {
        const isAuthenticated = await this.checkAuth();
        if (!isAuthenticated) {
            window.location.href = '/login';
            return;
        }

        const user = await this.getCurrentUser();
        if (user) {
            this.updateUserUI(user);
        }
    },

    // 更新用户UI
    updateUserUI(user) {
        const usernameElement = document.getElementById('username');
        const avatarElement = document.getElementById('userAvatar');

        if (usernameElement) {
            usernameElement.textContent = user.username;
        }

        if (avatarElement) {
            avatarElement.textContent = user.username.charAt(0).toUpperCase();
        }
    }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});