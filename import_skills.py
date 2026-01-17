#!/usr/bin/env python3
"""
Skills 数据导入脚本

使用方法:
1. 激活虚拟环境: source venv/bin/activate
2. 运行脚本: python import_skills.py /path/to/skills/directory
"""

import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Skill
from services.skill_service import SkillService


def main():
    if len(sys.argv) < 2:
        print("用法: python import_skills.py <skills_directory_path>")
        print("\n示例:")
        print("  python import_skills.py /Users/caoxupei/xinzhili/mall-pro/mall-multi/.claude/skills")
        sys.exit(1)

    skills_dir = sys.argv[1]

    if not os.path.exists(skills_dir):
        print(f"错误: 目录不存在: {skills_dir}")
        sys.exit(1)

    print(f"开始从目录导入 Skills: {skills_dir}")
    print("-" * 60)

    with app.app_context():
        try:
            # 创建表（如果不存在）
            db.create_all()
            print("✓ 数据库表已创建")

            # 批量导入
            skills = SkillService.batch_import_from_directory(skills_dir)

            print(f"\n✓ 成功导入 {len(skills)} 个 Skills:")
            print("-" * 60)

            for skill in skills:
                print(f"  • {skill.display_name or skill.name} ({skill.category})")
                print(f"    - 触发词: {len(skill.to_dict()['trigger_keywords'])} 个")
                print(f"    - Token: ~{skill.token_estimate}")
                print()

            print("-" * 60)
            print(f"✓ 导入完成！共 {len(skills)} 个 Skills")

        except Exception as e:
            print(f"\n✗ 导入失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()
