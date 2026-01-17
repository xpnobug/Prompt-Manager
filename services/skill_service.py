"""Skill 业务逻辑服务"""
import os
import json
from models import Skill, db
from utils import parse_skill_markdown, extract_trigger_keywords, estimate_tokens


class SkillService:
    """Skill 业务逻辑服务类"""

    @staticmethod
    def import_skill_from_file(file_path):
        """
        从 SKILL.md 文件导入

        Args:
            file_path (str): SKILL.md 文件路径

        Returns:
            Skill: Skill 对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        frontmatter, content = parse_skill_markdown(md_content)

        # 提取触发词
        trigger_keywords = extract_trigger_keywords(
            frontmatter.get('description', '')
        )

        # 估算 token
        token_estimate = estimate_tokens(content)

        # 处理 allowed-tools（可能是列表或字符串）
        allowed_tools = frontmatter.get('allowed-tools', [])
        if isinstance(allowed_tools, list):
            allowed_tools_json = json.dumps(allowed_tools)
        else:
            allowed_tools_json = '[]'

        # 从 frontmatter 读取分类，默认根据名称判断
        name = frontmatter.get('name', '')
        category = frontmatter.get('category', '')
        if not category:
            # 如果没有指定分类，根据名称自动判断
            if name.startswith('mall-'):
                category = 'project-specific'
            else:
                category = 'general'

        skill = Skill(
            name=name,
            display_name=frontmatter.get('name', ''),  # 可后续手动修改
            description=frontmatter.get('description', ''),
            model=frontmatter.get('model', ''),
            user_invocable=frontmatter.get('user-invocable', True),
            allowed_tools=allowed_tools_json,
            content=content,
            file_path=file_path,
            trigger_keywords=json.dumps(trigger_keywords, ensure_ascii=False),
            token_estimate=token_estimate,
            category=category,
            status='active',
            version='1.0'
        )

        return skill

    @staticmethod
    def import_from_content(filename, content):
        """
        从文件内容直接导入 Skill

        Args:
            filename (str): 文件名
            content (str): Markdown 文件内容

        Returns:
            Skill: Skill 对象
        """
        frontmatter, body = parse_skill_markdown(content)

        # 如果没有 name，使用文件名
        name = frontmatter.get('name', '')
        if not name:
            name = filename.replace('.md', '').replace('SKILL', '').strip('-_')

        # 提取触发词
        trigger_keywords = extract_trigger_keywords(
            frontmatter.get('description', '')
        )

        # 估算 token
        token_estimate = estimate_tokens(body)

        # 处理 allowed-tools
        allowed_tools = frontmatter.get('allowed-tools', [])
        if isinstance(allowed_tools, list):
            allowed_tools_json = json.dumps(allowed_tools)
        else:
            allowed_tools_json = '[]'

        # 从 frontmatter 读取分类，默认根据名称判断
        category = frontmatter.get('category', '')
        if not category:
            if name.startswith('mall-'):
                category = 'project-specific'
            else:
                category = 'general'

        # 检查是否已存在
        existing = Skill.query.filter_by(name=name).first()
        if existing:
            # 更新现有记录
            existing.description = frontmatter.get('description', '')
            existing.content = body
            existing.model = frontmatter.get('model', '')
            existing.user_invocable = frontmatter.get('user-invocable', True)
            existing.allowed_tools = allowed_tools_json
            existing.trigger_keywords = json.dumps(trigger_keywords, ensure_ascii=False)
            existing.token_estimate = token_estimate
            existing.category = category  # 更新分类
            db.session.commit()
            return existing
        else:
            # 创建新 Skill
            skill = Skill(
                name=name,
                display_name=name,
                description=frontmatter.get('description', ''),
                model=frontmatter.get('model', ''),
                user_invocable=frontmatter.get('user-invocable', True),
                allowed_tools=allowed_tools_json,
                content=body,
                file_path='uploaded',
                trigger_keywords=json.dumps(trigger_keywords, ensure_ascii=False),
                token_estimate=token_estimate,
                category=category,
                status='active',
                version='1.0'
            )
            db.session.add(skill)
            db.session.commit()
            return skill

    @staticmethod
    def batch_import_from_directory(skills_dir):
        """
        批量导入 skills 目录

        Args:
            skills_dir (str): Skills 目录路径

        Returns:
            list: 成功导入的 Skill 列表
        """
        skills = []

        if not os.path.exists(skills_dir):
            return skills

        # 方式1: 查找子目录中的 SKILL.md (标准结构)
        for skill_name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, skill_name)

            if not os.path.isdir(skill_path):
                continue

            md_file = os.path.join(skill_path, 'SKILL.md')
            if not os.path.exists(md_file):
                continue

            try:
                skill = SkillService.import_skill_from_file(md_file)

                # 如果 frontmatter 没有指定分类，则根据目录名判断
                if not skill.category:
                    if skill_name.startswith('mall-'):
                        skill.category = 'project-specific'
                    else:
                        skill.category = 'general'

                # 检查是否已存在
                existing = Skill.query.filter_by(name=skill.name).first()
                if existing:
                    # 更新现有记录
                    existing.description = skill.description
                    existing.content = skill.content
                    existing.model = skill.model
                    existing.user_invocable = skill.user_invocable
                    existing.allowed_tools = skill.allowed_tools
                    existing.trigger_keywords = skill.trigger_keywords
                    existing.token_estimate = skill.token_estimate
                    existing.file_path = skill.file_path
                    existing.category = skill.category
                    skills.append(existing)
                else:
                    db.session.add(skill)
                    skills.append(skill)

            except Exception as e:
                print(f"导入 {skill_name} 失败: {e}")
                continue

        # 方式2: 递归查找所有 SKILL.md 文件 (灵活结构)
        if len(skills) == 0:
            for root, dirs, files in os.walk(skills_dir):
                for filename in files:
                    if filename == 'SKILL.md' or filename.endswith('_SKILL.md'):
                        md_file = os.path.join(root, filename)
                        try:
                            skill = SkillService.import_skill_from_file(md_file)
                            
                            # 如果 frontmatter 没有指定分类，根据名称判断
                            if not skill.category:
                                if skill.name and skill.name.startswith('mall-'):
                                    skill.category = 'project-specific'
                                else:
                                    skill.category = 'general'

                            existing = Skill.query.filter_by(name=skill.name).first()
                            if existing:
                                existing.description = skill.description
                                existing.content = skill.content
                                existing.model = skill.model
                                existing.user_invocable = skill.user_invocable
                                existing.allowed_tools = skill.allowed_tools
                                existing.trigger_keywords = skill.trigger_keywords
                                existing.token_estimate = skill.token_estimate
                                existing.file_path = skill.file_path
                                existing.category = skill.category  # 同步更新分类
                                skills.append(existing)
                            else:
                                db.session.add(skill)
                                skills.append(skill)
                        except Exception as e:
                            print(f"导入 {md_file} 失败: {e}")
                            continue

        db.session.commit()
        return skills

    @staticmethod
    def search_skills(keyword=None, category=None, tags=None, page=1, per_page=20, sort='latest'):
        """
        搜索 Skills

        Args:
            keyword (str): 搜索关键词
            category (str): 分类筛选
            tags (list): 标签筛选
            page (int): 页码
            per_page (int): 每页数量
            sort (str): 排序方式 (latest/popular/name)

        Returns:
            dict: 分页结果
        """
        query = Skill.query.filter_by(status='active')

        # 关键词搜索（名称、描述）
        if keyword:
            keyword_filter = db.or_(
                Skill.name.contains(keyword),
                Skill.display_name.contains(keyword),
                Skill.description.contains(keyword),
                Skill.trigger_keywords.contains(keyword)
            )
            query = query.filter(keyword_filter)

        # 分类筛选
        if category:
            query = query.filter_by(category=category)

        # 排序
        if sort == 'popular':
            query = query.order_by(Skill.usage_count.desc(), Skill.views_count.desc())
        elif sort == 'name':
            query = query.order_by(Skill.name)
        else:  # latest
            query = query.order_by(Skill.created_at.desc())

        # 分页
        if per_page == -1:
            # 获取全部
            all_skills = query.all()
            return {
                'skills': all_skills,
                'total': len(all_skills),
                'page': 1,
                'per_page': len(all_skills),
                'pages': 1
            }

        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'skills': pagination.items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def get_skill_by_id(skill_id):
        """
        根据 ID 获取 Skill

        Args:
            skill_id (int): Skill ID

        Returns:
            Skill: Skill 对象
        """
        return Skill.query.get(skill_id)

    @staticmethod
    def increment_views(skill_id):
        """
        增加浏览计数

        Args:
            skill_id (int): Skill ID
        """
        skill = Skill.query.get(skill_id)
        if skill:
            skill.views_count += 1
            db.session.commit()

    @staticmethod
    def increment_usage(skill_id):
        """
        增加使用计数

        Args:
            skill_id (int): Skill ID
        """
        skill = Skill.query.get(skill_id)
        if skill:
            skill.usage_count += 1
            db.session.commit()

    @staticmethod
    def get_statistics():
        """
        获取统计信息

        Returns:
            dict: 统计数据
        """
        total = Skill.query.filter_by(status='active').count()
        general = Skill.query.filter_by(status='active', category='general').count()
        project_specific = Skill.query.filter_by(status='active', category='project-specific').count()

        most_viewed = Skill.query.filter_by(status='active').order_by(
            Skill.views_count.desc()
        ).limit(5).all()

        most_used = Skill.query.filter_by(status='active').order_by(
            Skill.usage_count.desc()
        ).limit(5).all()

        return {
            'total': total,
            'general': general,
            'project_specific': project_specific,
            'most_viewed': [s.to_dict() for s in most_viewed],
            'most_used': [s.to_dict() for s in most_used]
        }
