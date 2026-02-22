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




'''
查询功能
'''



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
    # 执行异步查询：从 Book 表中选取所有记录，返回包含 ORM 结果的 Result 对象
    result = await database.execute(select(Book))
    books = result.scalars().all()#获取所有数据
    #获取单条数据book = result.scalars().first()#获取第一条数据
    #get(模型类,主键值)的含义：根据主键值查询单条数据
    return {"books": books}

#查询条件:查询特定id的书籍(比较判断)
@app.get("/book/books/{id}")
async def get_book(id: int, database=Depends(get_database)):
    # 从数据库会话中查询所有书籍
    result = await database.execute(select(Book).where(Book.id == id))#返回一个orm对象，await是异步操作，多线程操作，等待数据库返回结果
    book = result.scalar_one_or_none()#获取单条数据，如果没有则返回None
    #get(模型类,主键值)的含义：根据主键值查询单条数据
    return {"book": book}

#模糊查询:作者以曹开头(like判断)(%多个字符,_单个字符)(&,|,~与非判断)(in_()包含判断)
@app.get("/book/author")
async def get_search_author(
    database=Depends(get_database)
):
    result = await database.execute(select(Book).where(Book.author.like("曹%")&(Book.price>100)))
    books = result.scalars().all()#获取所有数据
    return {"books": books}


#聚合查询(func.方法(模型类.属性)(方法:cout,sum,avg,max,min...))
@app.get("/book/price")
async def get_price(
    database=Depends(get_database)
):
    result = await database.execute(select(func.count(Book.id),func.sum(Book.price),func.avg(Book.price),func.max(Book.price),func.min(Book.price)))
    price = result.scalars().all()#获取所有数据
    return {"price": price}




#分页查询(select().offset().limit())
@app.get("/book/page")
async def get_page(
    database=Depends(get_database)
):
    limit = 2
    #页码—1*每页数量=跳过的数量
    skip = (limit-1)*10
    result = await database.execute(select(Book).offset(skip).limit(10))
    books = result.scalars().all()#获取所有数据
    return {"books": books}





'''
新增功能(类似git操作命令)
使用post功能来添加数据
'''
# 1. 定义路由：POST /books
# 2. 定义请求体模型：BookCreate
# 3. 从请求体中提取数据：book_create = await request.json()
# 4. 创建新书籍实例：book = Book(**book_create.dict())
# 5. 添加到数据库会话：session.add(book)
# 6. 提交事务：await session.commit()
# 7. 返回新创建的书籍：return {"book": book}

#用户输入图书信息（id，书名，作者，价格）
class BookCreate(BaseModel):
    id: int
    title: str
    author: str
    price: float


@app.get("book/create_book")
async def create_book(
    database=Depends(get_database),
    book = BookCreate
):
    #创建新书籍实例：book = Book(**book_create.dict())(orm对象)
    book_obj = Book(**book.dict())
    database.add(book_obj)
    # 提交事务
    await database.commit()
    # 返回新创建的书籍
    return {"book": book}



'''
 更新功能(类git)(先查再更新,提交)
 使用put功能
'''   
class BookUpdate(BaseModel):
    title: str
    author: str
    price: float

@app.put("/book/update_book/{id}")
async def update_book(
    id: int,
    database=Depends(get_database),
    book = BookUpdate
):
    # 从数据库会话中查询所有书籍
    result = await database.get(Book,id)#返回一个orm对象，await是异步操作，多线程操作，等待数据库返回结果
    book_obj = result.scalar_one_or_none()#获取单条数据，如果没有则返回None
    if book_obj is None:
        return {"error": "Book not found"}
    # 更新书籍属性
    book_obj.title = book.title
    book_obj.author = book.author
    book_obj.price = book.price
    # 提交事务
    await database.commit()
    # 返回更新后的书籍
    return {"book": book_obj}




'''
删除功能(先查再删,提交)
'''

@app.delete("/book/delete_book/{id}")
async def delete_book(
    id: int,
    database=Depends(get_database)
):
    # 从数据库会话中查询所有书籍
    result = await database.get(Book,id)#返回一个orm对象，await是异步操作，多线程操作，等待数据库返回结果
    book_obj = result.scalar_one_or_none()#获取单条数据，如果没有则返回None
    if book_obj is None:
        return {"error": "Book not found"}
    # 删除书籍
    await database.delete(book_obj)
    # 提交事务
    await database.commit()
    # 返回删除后的书籍
    return {"book": book_obj}
