import os
import time
from sqlalchemy import inspect, text  # <--- 1. 这里加了 text
from werkzeug.security import generate_password_hash
from flask_migrate import migrate, upgrade, init, stamp

# 引入你的应用组件
from app import create_app, db
from models import User

# 创建应用上下文
app = create_app()


def ensure_admin_user():
    """
    [幂等性] 检查并创建管理员账户，确保系统初始化后立即可用。
    """
    admin_username = app.config.get('ADMIN_USERNAME', 'admin')

    try:
        user = User.query.filter_by(username=admin_username).first()
    except Exception:
        return

    if not user:
        print(f"👤 [System] 正在创建管理员账户: {admin_username} ...")
        admin_password = app.config.get('ADMIN_PASSWORD', '123456')
        admin = User(username=admin_username, password_hash=generate_password_hash(admin_password))
        db.session.add(admin)
        db.session.commit()
        print("✅ 管理员账户创建成功！")
    else:
        print(f"✅ 管理员账户 '{admin_username}' 已存在。")


def sync_database():
    """
    [核心逻辑] 智能数据库同步工具 (已增强自动修复功能)
    """
    print("=" * 60)
    print("🛠️  Prompt Manager 智能数据库同步工具 (Smart Sync)")
    print("=" * 60)

    with app.app_context():
        # 1. 检查数据库连接与表状态
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            db_path = str(db.engine.url)
            print(f"📂 数据库目标: {db_path}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return

        # 2. 初始化迁移仓库 (如果不存在)
        # 标记是否刚刚执行了初始化，用于后续判断是否需要重置 DB 版本
        is_fresh_migrations = False

        if not os.path.exists('migrations'):
            print("📦 检测到 migrations 文件夹缺失 (可能是 Docker 镜像更新导致)...")
            print("⚙️  正在重新初始化迁移环境...")
            init()
            is_fresh_migrations = True

        # 3. 智能处理版本冲突
        has_version_table = 'alembic_version' in existing_tables

        if has_version_table and is_fresh_migrations:
            print("⚠️  [自动修复] 检测到数据库有历史记录，但迁移文件已丢失。")
            print("🔄 正在重置数据库版本记录，以匹配当前代码...")
            # 强制删除版本表
            with db.engine.connect() as conn:
                conn.execute(text("DROP TABLE alembic_version"))
                conn.commit()
            print("✅ 版本记录已重置。")
            has_version_table = False  # 更新状态

        # 4. 处理“既有表但无版本号”的情况 (Stamping)
        if 'user' in existing_tables and not has_version_table:
            print("🏷️  正在将当前数据库状态标记为基准版本 (Stamping)...")
            # 注意：如果你的 Model 比 数据库 新，后续的 migrate 会自动检测出差异
            stamp()

        # 5. 处理版本冲突 & 应用迁移
        print("🔍 正在检查数据库迁移状态...")

        # 先检查是否有无效的版本记录
        if has_version_table:
            try:
                # 尝试 upgrade，如果版本无效会报错
                upgrade()
                print("✅ 数据库迁移状态正常。")
            except Exception as e:
                error_msg = str(e)
                if "Can't locate revision" in error_msg or "Target database is not up to date" in error_msg:
                    print(f"⚠️  [自动修复] 检测到无效的迁移版本记录...")
                    print("🔄 正在重置迁移版本表...")
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
                            conn.commit()
                        print("✅ 版本表已删除。")
                        
                        # 重新标记当前数据库状态
                        print("🏷️  正在重新标记数据库状态 (Stamping)...")
                        stamp()
                        print("✅ 数据库状态已标记为最新。")
                    except Exception as e2:
                        print(f"❌ 重置失败: {e2}")
                        print("⚠️  请手动执行: DROP TABLE alembic_version;")
                else:
                    print(f"ℹ️  升级提示: {e}")

        # 6. 检测新的模型变更
        try:
            # 使用时间戳防止迁移脚本文件名冲突
            migration_message = f"auto_update_{int(time.time())}"
            migrate(message=migration_message)
            print("📝 检测到新变更，已生成迁移脚本。")

            # 应用新生成的迁移
            upgrade()
            print("✅ 数据库结构已同步至最新。")
        except Exception as e:
            # "No changes in schema detected" 是正常情况
            if "No changes" not in str(e):
                print(f"ℹ️  迁移提示: {e}")

        # 6. 确保种子数据 (管理员)
        ensure_admin_user()

    print("\n🎉 所有操作完成！系统已就绪。")


if __name__ == '__main__':
    try:
        sync_database()
    except KeyboardInterrupt:
        print("\n🚫 操作已取消。")
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")