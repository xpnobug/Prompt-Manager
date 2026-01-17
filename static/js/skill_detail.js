/**
 * Skill 详情页面交互逻辑 (重构版)
 * 与 gallery.js 风格一致
 */

// 使用 marked.js 渲染 Markdown（简化版）
function renderMarkdown(markdown) {
    let html = markdown;

    // 代码块
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang || 'text'}">${escapeHtml(code.trim())}</code></pre>`;
    });

    // 行内代码
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // 标题
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // 粗体
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // 斜体
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // 无序列表
    html = html.replace(/^\- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // 有序列表
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // 链接
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

    // 换行
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 复制 Skill 名称
function copySkillName() {
    const name = skillData.name;
    copyToClipboard(name, '复制 Skill 名称', 'Skill 名称已复制');
}

// 复制 Markdown 内容
function copyMarkdown() {
    const markdown = skillData.content;
    copyToClipboard(markdown, '复制', 'Markdown 已复制', 'btnCopyMarkdown');
}

// 标记为已使用
async function markAsUsed() {
    try {
        const response = await fetch(`/api/skills/${skillData.id}/usage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        });

        const data = await response.json();

        if (data.success) {
            showToast('已标记为使用', 'success');

            // 更新显示的使用次数
            const usageElement = document.getElementById('stat-usage');
            if (usageElement) {
                const currentUsage = parseInt(usageElement.textContent);
                usageElement.textContent = currentUsage + 1;
            }
        } else {
            showToast(data.message || '操作失败', 'danger');
        }
    } catch (error) {
        console.error('标记失败:', error);
        showToast('操作失败，请稍后重试', 'danger');
    }
}

// 复制到剪贴板 (带动画反馈)
function copyToClipboard(text, originalText, successText, btnId) {
    const btn = btnId ? document.getElementById(btnId) : null;

    const onSuccess = () => {
        if (btn) {
            const originalHtml = btn.innerHTML;

            // 极简反馈：变图标和文字
            btn.innerHTML = '<i class="bi bi-check2 me-1"></i> <span>' + successText + '</span>';
            btn.classList.remove('text-secondary');
            btn.classList.add('text-success');

            // 2秒后恢复
            setTimeout(() => {
                btn.innerHTML = '<i class="bi bi-clipboard me-1"></i> <span>' + originalText + '</span>';
                btn.classList.remove('text-success');
                btn.classList.add('text-secondary');
            }, 2000);
        } else {
            showToast(successText, 'success');
        }
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(onSuccess).catch(err => {
            console.error('复制失败:', err);
            fallbackCopyToClipboard(text, onSuccess);
        });
    } else {
        fallbackCopyToClipboard(text, onSuccess);
    }
}

// 备用复制方法
function fallbackCopyToClipboard(text, callback) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        if (callback) callback();
    } catch (err) {
        console.error('备用复制失败:', err);
        showToast('复制失败，请手动复制', 'danger');
    }

    document.body.removeChild(textArea);
}

// 显示提示消息 (Apple 风格)
function showToast(message, type = 'info') {
    // 移除已有的 toast
    document.querySelectorAll('.toast-apple').forEach(el => el.remove());

    const toast = document.createElement('div');
    toast.className = 'toast-apple';
    toast.innerHTML = `
        <div class="d-flex align-items-center" style="
            background: var(--sidebar-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(128,128,128,0.1);
            border-radius: 100px;
            padding: 12px 24px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.12);
            color: var(--text-primary);
        ">
            <i class="bi bi-${type === 'success' ? 'check-circle-fill text-success' : 'exclamation-triangle-fill text-warning'} me-2"></i>
            ${message}
        </div>
    `;

    toast.style.cssText = `
        position: fixed;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        animation: slideDown 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s, transform 0.3s';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(-10px)';
        setTimeout(() => {
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// 页面加载完成后渲染 Markdown
document.addEventListener('DOMContentLoaded', () => {
    const markdownContainer = document.getElementById('skill-markdown');

    if (skillData && skillData.content) {
        markdownContainer.innerHTML = renderMarkdown(skillData.content);
    } else {
        markdownContainer.innerHTML = '<p class="text-muted">暂无内容</p>';
    }
});