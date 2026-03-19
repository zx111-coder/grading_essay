# test_db_save.py
import sys
import os
from datetime import datetime
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_mock_engine, create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.essays import Essay
from app.models.comments import Comment
from app.schemas.essays import EssayCreate
from app.schemas.comments import CommentCreate
from app.services.database_service import DataService

# 模拟的作文数据（基于你的真实数据）
TEST_CORRECTION_DATA = {
    'title': '一起听蛙',
    'words_count': 699,
    'requirements': '倾听，就是集中精力，开动脑筋，认真听取。一个谦虚好学的人...',
    'grade': 3,
    'upload_time': '2026-02-21 19:03',
    'paragraphs': ['一起听蛙', '第一段内容...', '第二段内容...'],
    'comment': '这是一篇优秀的作文...',
    'scores': {'score': 92, 'content': 33, 'structure': 18, 'language': 23, 'basic': 18},
    'sum': '同学，你的作文非常优秀...'
}


def setup_test_database():
    """创建测试数据库（使用SQLite内存数据库）"""
    # 使用SQLite内存数据库，不需要真实数据库
    engine = create_engine('sqlite:///:memory:', echo=True)

    # 创建所有表
    from app.models.essays import Base as EssaysBase
    from app.models.comments import Base as CommentsBase

    EssaysBase.metadata.create_all(bind=engine)
    CommentsBase.metadata.create_all(bind=engine)

    # 创建会话工厂
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return TestingSessionLocal


def test_save_essay_only():
    """测试只保存作文"""
    print("\n" + "=" * 60)
    print("测试1: 只保存作文")
    print("=" * 60)

    # 设置测试数据库
    TestingSessionLocal = setup_test_database()
    db = TestingSessionLocal()

    try:
        # 创建Essay数据
        essay_data = EssayCreate(
            user_id=1,  # 测试用的user_id
            word_count=TEST_CORRECTION_DATA["words_count"],
            upload_date=datetime.strptime(TEST_CORRECTION_DATA["upload_time"], "%Y-%m-%d %H:%M"),
            grade=TEST_CORRECTION_DATA["grade"],
            requirement=TEST_CORRECTION_DATA["requirements"],
            title=TEST_CORRECTION_DATA["title"],
            paragraphs=TEST_CORRECTION_DATA["paragraphs"]
        )

        print(f"📝 准备保存Essay数据:")
        print(f"   - user_id: {essay_data.user_id}")
        print(f"   - title: {essay_data.title}")
        print(f"   - word_count: {essay_data.word_count}")

        # 保存到数据库
        saved_essay = DataService.save_essay(db, essay_data)
        db.commit()

        print(f"✅ Essay保存成功!")
        print(f"   - ID: {saved_essay.id}")
        print(f"   - 类型: {type(saved_essay)}")

        # 验证是否真的保存了
        from_db = db.query(Essay).filter(Essay.id == saved_essay.id).first()
        if from_db:
            print(f"✅ 验证成功: 可以从数据库查询到Essay ID {from_db.id}")
        else:
            print(f"❌ 验证失败: 无法从数据库查询到Essay")

        return saved_essay.id

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()


def test_save_comment_only(essay_id):
    """测试只保存批改结果"""
    print("\n" + "=" * 60)
    print("测试2: 保存批改结果")
    print("=" * 60)

    # 设置测试数据库
    TestingSessionLocal = setup_test_database()
    db = TestingSessionLocal()

    try:
        # 创建Comment数据
        comment_data = CommentCreate(
            essay_id=essay_id,
            comment_details=TEST_CORRECTION_DATA["comment"],
            scores=TEST_CORRECTION_DATA["scores"],
            sum=TEST_CORRECTION_DATA["sum"]
        )

        print(f"📝 准备保存Comment数据:")
        print(f"   - essay_id: {comment_data.essay_id}")
        print(f"   - comment_details长度: {len(comment_data.comment_details) if comment_data.comment_details else 0}")
        print(f"   - scores: {comment_data.scores}")
        print(f"   - sum长度: {len(comment_data.sum) if comment_data.sum else 0}")

        # 保存到数据库
        saved_comment = DataService.save_comment(db, comment_data)
        db.commit()

        print(f"✅ Comment保存成功!")
        print(f"   - ID: {saved_comment.id}")
        print(f"   - essay_id: {saved_comment.essay_id}")

        # 验证是否真的保存了
        from_db = db.query(Comment).filter(Comment.id == saved_comment.id).first()
        if from_db:
            print(f"✅ 验证成功: 可以从数据库查询到Comment ID {from_db.id}")
            print(f"   - 存储的comment_details长度: {len(from_db.comment_details) if from_db.comment_details else 0}")
        else:
            print(f"❌ 验证失败: 无法从数据库查询到Comment")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def test_save_both_together():
    """测试一起保存作文和批改结果（模拟真实场景）"""
    print("\n" + "=" * 60)
    print("测试3: 一起保存作文和批改结果")
    print("=" * 60)

    # 设置测试数据库
    TestingSessionLocal = setup_test_database()
    db = TestingSessionLocal()

    try:
        # 1. 先保存作文
        essay_data = EssayCreate(
            user_id=1,
            word_count=TEST_CORRECTION_DATA["words_count"],
            upload_date=datetime.strptime(TEST_CORRECTION_DATA["upload_time"], "%Y-%m-%d %H:%M"),
            grade=TEST_CORRECTION_DATA["grade"],
            requirement=TEST_CORRECTION_DATA["requirements"],
            title=TEST_CORRECTION_DATA["title"],
            paragraphs=TEST_CORRECTION_DATA["paragraphs"]
        )

        print("步骤1: 保存Essay...")
        saved_essay = DataService.save_essay(db, essay_data)
        print(f"   ✅ Essay保存成功，ID: {saved_essay.id}")

        # 2. 再保存批改结果
        comment_data = CommentCreate(
            essay_id=saved_essay.id,
            comment_details=TEST_CORRECTION_DATA["comment"],
            scores=TEST_CORRECTION_DATA["scores"],
            sum=TEST_CORRECTION_DATA["sum"]
        )

        print("步骤2: 保存Comment...")
        saved_comment = DataService.save_comment(db, comment_data)
        print(f"   ✅ Comment保存成功，ID: {saved_comment.id}")

        # 3. 提交事务
        print("步骤3: 提交事务...")
        db.commit()
        print("   ✅ 事务提交成功")

        # 4. 验证数据
        print("步骤4: 验证数据...")
        essay_from_db = db.query(Essay).filter(Essay.id == saved_essay.id).first()
        comment_from_db = db.query(Comment).filter(Comment.essay_id == saved_essay.id).first()

        if essay_from_db and comment_from_db:
            print("   ✅ 验证成功: 两条数据都成功保存")
            print(f"   - Essay ID: {essay_from_db.id}, 标题: {essay_from_db.title}")
            print(f"   - Comment ID: {comment_from_db.id}, 关联Essay ID: {comment_from_db.essay_id}")
        else:
            print("   ❌ 验证失败: 数据保存不完整")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def test_with_missing_fields():
    """测试缺少字段的情况"""
    print("\n" + "=" * 60)
    print("测试4: 测试缺少字段的情况")
    print("=" * 60)

    TestingSessionLocal = setup_test_database()
    db = TestingSessionLocal()

    try:
        # 创建缺少必要字段的数据
        incomplete_data = {
            'title': '测试标题',
            'user_id': 1,
            # 缺少 word_count, upload_date 等
        }

        essay_data = EssayCreate(
            user_id=1,
            word_count=None,  # 允许为空的字段
            upload_date=None,  # 允许为空的字段
            grade=3,  # 必须有的字段
            requirement=None,
            title="测试标题",
            paragraphs=["段落1"]  # 必须有的字段
        )

        print("尝试保存缺少可选字段的数据...")
        saved_essay = DataService.save_essay(db, essay_data)
        db.commit()

        print(f"✅ 保存成功! ID: {saved_essay.id}")
        print("说明: 可选字段为None是可以的")

    except Exception as e:
        print(f"❌ 保存失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


def test_foreign_key_constraint():
    """测试外键约束"""
    print("\n" + "=" * 60)
    print("测试5: 测试外键约束")
    print("=" * 60)

    TestingSessionLocal = setup_test_database()
    db = TestingSessionLocal()

    try:
        # 尝试保存一个不存在的essay_id的comment
        comment_data = CommentCreate(
            essay_id=999,  # 不存在的ID
            comment_details="测试评论",
            scores={"score": 90},
            sum="总结"
        )

        print("尝试保存不存在的essay_id的comment...")
        saved_comment = DataService.save_comment(db, comment_data)
        db.commit()

        print("⚠️  这不应该成功，但没有报错？")

    except Exception as e:
        print(f"✅ 预期的错误发生: {str(e)}")
        print("说明: 外键约束正常工作")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("开始测试数据库保存功能")
    print("=" * 60)

    # 运行测试1
    essay_id = test_save_essay_only()

    # 运行测试2（需要测试1的essay_id）
    if essay_id:
        test_save_comment_only(essay_id)

    # 运行测试3
    test_save_both_together()

    # 运行测试4
    test_with_missing_fields()

    # 运行测试5
    test_foreign_key_constraint()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
