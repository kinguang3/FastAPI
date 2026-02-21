import datetime
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from sqlalchemy import DateTime, func, String, Float, select
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker,async_session

#1.创建异步数据库引擎
engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    echo=True,#可选，输出SQL日志
    pool_size = 10,#设置连接池活跃的连接数
    max_overflow = 20#允许额外的连接数
    )


#2.定义模型类：基类+表对应的模型类

#基类：创建时间+更新时间；书籍表：id，书名，作者，价格，创建时间，更新时间
class Base(DeclarativeBase):
    # 创建时间字段：首次插入时自动写入当前时间
    creat_time: Mapped[datetime] = mapped_column(
        DateTime,
        insert_default=func.now(),  # 仅在 INSERT 时生效
        default=func.now,            # 同时作为 Python 默认值
        comment="创建时间"
    )
    # 更新时间字段：首次插入时自动写入当前时间
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        insert_default=func.now(),  # 仅在 INSERT 时生效
        default=func.now,            # 同时作为 Python 默认值
        comment="更新时间"
    )

#表对应的模型类
class Book(Base):
    __tablename__ = "books"  #表名
    # 主键字段：id
    id: Mapped[int] = mapped_column(
        primary_key=True,
        comment="主键ID"
    )
    # 书名字段：不能为空
    title: Mapped[str] = mapped_column(
        String(255),
        comment="书名"
    )
    # 作者字段：不能为空
    author: Mapped[str] = mapped_column(
        String(255),
        comment="作者"
    )
    # 价格字段：不能为空
    price: Mapped[float] = mapped_column(
        Float,
        comment="价格"
    )




# lifespan 上下文管理器（替代弃用的 on_event）
@asynccontextmanager
async def lifespan(app: FastAPI):


    # 启动时执行：创建数据库表

    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时执行（可选）

#创建FastAPI实例
app = FastAPI(lifespan=lifespan)


#查询功能
#查询功能的接口，查询图书 -> 依赖注入：创建依赖项获取数据库会话+Depends 注入路由处理函数
#创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine, #绑定数据库引擎
    class_=AsyncSession,  #指定会话类
    expire_on_commit=False  # 提交后不过期，保持会话状态
)

#依赖项
async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session  #返回数据库会话给路由处理函数
            await session.commit() #提交事务
        except Exception:
            await session.rollback()  # 回滚
            raise  # 重新抛出异常
        finally:
            await session.close()  # 关闭会话


@app.get("/book/books")
async def get_books(database=Depends(get_database)):
    # 从数据库会话中查询所有书籍
    result = await database.execute(select(Book))
    books = result.scalars().all()
    return {"books": books}
    