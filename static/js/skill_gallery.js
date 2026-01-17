/**
 * Skills 画廊页面交互逻辑 (重构版)
 * 与 gallery.js 风格一致
 */

let currentPage = 1;
let currentCategory = '';
let currentKeyword = '';
let currentSort = 'latest';

// 加载 Skills
async function loadSkills(page = 1) {
    const params = new URLSearchParams({
        page: page,
        per_page: 20,
        category: currentCategory,
        q: currentKeyword,
        sort: currentSort
    });

    try {
        const response = await fetch(`/api/skills?${params}`);
        const data = await response.json();

        if (data.success) {
            renderSkills(data.data.skills);
            renderPagination(data.data.page, data.data.pages, data.data.total);
            updatePageInfo(data.data.total);
            currentPage = data.data.page;
        }
    } catch (error) {
        console.error('加载 Skills 失败:', error);
        showError('加载失败，请稍后重试');
    }
}

// 渲染 Skills 瀑布流
function renderSkills(skills) {
    const grid = document.getElementById('skills-grid');

    if (!skills || skills.length === 0) {
        grid.innerHTML = `
            <div class="text-center py-5 w-100" style="color: var(--text-secondary); break-inside: avoid;">
                <i class="bi bi-inbox fs-1 opacity-25"></i>
                <p class="mt-3">暂无 Skills</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = skills.map(skill => createSkillCard(skill)).join('');
}

// 创建 Skill 卡片 (Apple 风格)
function createSkillCard(skill) {
    const categoryIcon = skill.category === 'general' ? 'bi-gear-fill' : 'bi-folder-fill';
    const categoryName = skill.category === 'general' ? '通用' : '项目特定';
    const keywords = skill.trigger_keywords ? skill.trigger_keywords.slice(0, 3) : [];

    // 截断描述
    let shortDesc = skill.description || '';
    const firstSentence = shortDesc.split('。')[0];
    shortDesc = firstSentence.length > 80 ? firstSentence.substring(0, 80) + '...' : firstSentence + (shortDesc.includes('。') ? '。' : '');

    return `
        <div class="skill-item group">
            <div class="skill-frame" onclick="location.href='/skills/${skill.id}'">
                <!-- 头部：分类标签 -->
                <div class="skill-header">
                    <span class="skill-category-badge">
                        <i class="bi ${categoryIcon} me-1"></i>${categoryName}
                    </span>
                    ${skill.tier ? `<span class="skill-tier-badge">${skill.tier}</span>` : ''}
                </div>

                <!-- 标题 -->
                <h3 class="skill-title">${skill.display_name || skill.name}</h3>

                <!-- 描述 -->
                <p class="skill-desc">${shortDesc}</p>

                <!-- 触发词标签 -->
                ${keywords.length > 0 ? `
                <div class="skill-tags">
                    ${keywords.map(kw => `<span class="mini-tag"><i class="bi bi-tag-fill me-1 opacity-50"></i>${kw}</span>`).join('')}
                </div>
                ` : ''}

                <!-- 统计信息 -->
                <div class="skill-stats">
                    <span><i class="bi bi-eye-fill me-1"></i>${skill.views_count || 0}</span>
                    <span><i class="bi bi-graph-up me-1"></i>${skill.usage_count || 0}</span>
                    <span><i class="bi bi-file-text me-1"></i>~${skill.token_estimate || 0}</span>
                </div>
            </div>
        </div>
    `;
}

// 更新页面信息
function updatePageInfo(total) {
    const countEl = document.getElementById('skills-count');
    const titleEl = document.getElementById('page-title');

    let categoryText = 'Skills 市场';
    if (currentCategory === 'general') {
        categoryText = '通用 Skills';
    } else if (currentCategory === 'project-specific') {
        categoryText = '项目特定';
    }

    if (currentKeyword) {
        categoryText = `搜索: "${currentKeyword}"`;
    }

    titleEl.textContent = categoryText;
    countEl.textContent = `${total} 个 Skills`;
}

// 渲染分页 (现代化样式)
function renderPagination(currentPage, totalPages, totalItems) {
    const container = document.getElementById('pagination-container');
    const pagination = document.getElementById('pagination');

    if (totalPages <= 1) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'flex';

    let html = '';

    // 上一页
    html += `
        <a class="page-link-item ${currentPage === 1 ? 'disabled' : ''}"
           href="#" onclick="loadSkills(${currentPage - 1}); return false;" title="Previous">
            <i class="bi bi-chevron-left small"></i>
        </a>
    `;

    // 页码
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    if (startPage > 1) {
        html += `<a class="page-link-item" href="#" onclick="loadSkills(1); return false;">1</a>`;
        if (startPage > 2) {
            html += `<span class="page-ellipsis"><i class="bi bi-three-dots"></i></span>`;
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            html += `<span class="page-link-item active">${i}</span>`;
        } else {
            html += `<a class="page-link-item" href="#" onclick="loadSkills(${i}); return false;">${i}</a>`;
        }
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<span class="page-ellipsis"><i class="bi bi-three-dots"></i></span>`;
        }
        html += `<a class="page-link-item" href="#" onclick="loadSkills(${totalPages}); return false;">${totalPages}</a>`;
    }

    // 下一页
    html += `
        <a class="page-link-item ${currentPage === totalPages ? 'disabled' : ''}"
           href="#" onclick="loadSkills(${currentPage + 1}); return false;" title="Next">
            <i class="bi bi-chevron-right small"></i>
        </a>
    `;

    pagination.innerHTML = html;
}

// 显示错误
function showError(message) {
    const grid = document.getElementById('skills-grid');
    grid.innerHTML = `
        <div class="text-center py-5 w-100" style="color: var(--text-secondary); break-inside: avoid;">
            <i class="bi bi-exclamation-triangle-fill fs-1 text-danger opacity-50"></i>
            <p class="mt-3">${message}</p>
        </div>
    `;
}

// 分类筛选
function filterByCategory(category) {
    currentCategory = category;
    currentPage = 1;

    // 更新侧边栏激活状态
    document.querySelectorAll('.nav-item-apple[data-category]').forEach(el => {
        el.classList.toggle('active', el.dataset.category === category);
    });

    loadSkills(1);
}

// 排序
function sortBy(sort) {
    currentSort = sort;
    currentPage = 1;

    // 更新排序控件激活状态
    document.querySelectorAll('.segmented-control .nav-link').forEach(el => {
        el.classList.toggle('active', el.dataset.sort === sort);
    });

    loadSkills(1);
}

// 搜索防抖
let searchTimeout = null;
document.getElementById('search-input').addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentKeyword = e.target.value.trim();
        currentPage = 1;
        loadSkills(1);
    }, 300);
});

// 初始加载
document.addEventListener('DOMContentLoaded', () => {
    loadSkills(1);
});