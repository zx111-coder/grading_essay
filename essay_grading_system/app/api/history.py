from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.essays import Essay
from app.models.comments import Comment
from datetime import datetime  # 添加这个导入

router = APIRouter()


@router.get('/history/{user_id}')
async def get_user_history(
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        title: str = None,  # 新增：标题搜索关键字
        start_date: str = None,  # 新增：开始日期
        end_date: str = None,  # 新增：结束日期
        db: Session = Depends(get_db)
):
    """获取用户的历史记录（分页），支持搜索和日期筛选"""

    # 构建基础查询
    query = db.query(Essay).filter(Essay.user_id == user_id)

    # 1. 标题搜索（模糊匹配）
    if title:
        query = query.filter(Essay.title.contains(title))

    # 2. 日期范围搜索
    if start_date:
        try:
            # 将字符串转换为日期对象
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Essay.upload_date >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误，应为 YYYY-MM-DD")

    if end_date:
        try:
            # 将结束日期设为当天的23:59:59，包含整天
            end = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            query = query.filter(Essay.upload_date <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误，应为 YYYY-MM-DD")

    # 查询总数
    total = query.count()

    # 计算偏移量
    offset = (page - 1) * page_size

    # 查询作文列表（按时间倒序）
    essays = query.order_by(Essay.upload_date.desc()) \
        .offset(offset) \
        .limit(page_size) \
        .all()

    # 构建返回数据
    history_list = []
    for essay in essays:
        comment = db.query(Comment).filter(Comment.essay_id == essay.id).first()
        history_list.append({
            "id": essay.id,
            "title": essay.title,
            "upload_date": essay.upload_date,
            "grade": essay.grade,
            "word_count": essay.word_count,
            "score": comment.scores.get("score") if comment and comment.scores else None,
            "summary": comment.sum[:50] + "..." if comment and comment.sum else "暂无批改",
            "task_id": essay.task_id 
        })

    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": history_list
        }
    }


@router.get('/history/detail/{essay_id}')
async def get_history_detail(essay_id: int, db: Session = Depends(get_db)):
    """获取单条历史记录的详细信息"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")

    comment = db.query(Comment).filter(Comment.essay_id == essay_id).first()

    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "essay": {
                "id": essay.id,
                "title": essay.title,
                "content": "\n".join(essay.paragraphs) if essay.paragraphs else "",
                "upload_date": essay.upload_date,
                "grade": essay.grade,
                "word_count": essay.word_count,
                "requirement": essay.requirement
            },
            "comment": {
                "details": comment.comment_details if comment else None,
                "scores": comment.scores if comment else None,
                "sum": comment.sum if comment else None
            }
        }
    }


@router.delete('/history/{essay_id}')
async def delete_history(essay_id: int, db: Session = Depends(get_db)):
    """删除历史记录（同时删除作文和对应的批改）"""

    # 查询作文是否存在
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")

    try:
        # 先删除关联的批改记录（如果有）
        comment = db.query(Comment).filter(Comment.essay_id == essay_id).first()
        if comment:
            db.delete(comment)
            db.flush()  # 先提交删除批改，确保外键约束

        # 再删除作文
        db.delete(essay)
        db.commit()

        return {
            "code": 200,
            "message": "删除成功",
            "data": {
                "id": essay_id,
                "title": essay.title
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败：{str(e)}")


@router.put('/history/{essay_id}/title')  # 必须完全匹配前端的 URL
async def update_history_title(essay_id: int, request: dict, db: Session = Depends(get_db)):
    """修改历史记录的标题"""

    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文不存在")

    title = request.get('title')
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")

    try:
        essay.title = title
        db.commit()

        return {
            "code": 200,
            "message": "标题修改成功",
            "data": {
                "id": essay.id,
                "title": essay.title
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改失败：{str(e)}")


@router.delete('/history/batch')
async def batch_delete_history(essay_ids: list[int], db: Session = Depends(get_db)):
    """批量删除历史记录"""

    if not essay_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的记录")

    try:
        deleted_count = 0
        failed_ids = []

        for essay_id in essay_ids:
            essay = db.query(Essay).filter(Essay.id == essay_id).first()
            if essay:
                # 先删除关联的批改
                comment = db.query(Comment).filter(Comment.essay_id == essay_id).first()
                if comment:
                    db.delete(comment)
                    db.flush()

                # 删除作文
                db.delete(essay)
                deleted_count += 1
            else:
                failed_ids.append(essay_id)

        db.commit()

        return {
            "code": 200,
            "message": f"成功删除 {deleted_count} 条记录",
            "data": {
                "success_count": deleted_count,
                "failed_ids": failed_ids
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除失败：{str(e)}")
