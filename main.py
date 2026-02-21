'''

fastapi作用
1. 快速创建api
2. 快速创建api
3. 自动生成api文档
4. 支持异步请求
5. 支持依赖注入
6. 支持中间件
7. 支持插件扩展


异步的定义
1. 异步函数是指在执行过程中可以暂停并等待其他操作完成的函数。
2. 异步函数通常用于处理I/O操作，例如数据库查询、网络请求等，以避免阻塞主线程。
3. 在FastAPI中，异步函数可以使用async和await关键字来定义和调用。
4. 异步函数可以在路由处理函数中使用，也可以在依赖注入中使用。
5. 异步函数可以与同步函数混合使用，以实现更复杂的业务逻辑。

'''
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI,Path,Query,Depends# 导入Request类，导包
from pydantic import BaseModel,Field# 导入BaseModel类，用于定义请求体参数的模型
from fastapi.responses import HTMLResponse,FileResponse,StreamingResponse
from sqlalchemy import DateTime, func, String, Float
from sqlalchemy.orm import polymorphic_union# 导入HTMLResponse类，用于返回HTML内容.导入FileResponse类，用于返回文件内容.导入StreamingResponse类

'''
ORM模型
安装:-m pip install sqlalchemy aiosqlite
'''
from sqlalchemy.ext.asyncio import create_async_engine

#1.创建异步数据库引擎
engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    echo=True,#可选，输出SQL日志
    pool_size = 10,#设置连接池活跃的连接数
    max_overflow = 20#允许额外的连接数
    )


#2.定义模型类：基类+表对应的模型类
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column

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

@app.get("/")#async异步路由,get是fastapi实例的请求方法,"/"是请求路径,root是路由处理函数
async def root():#请求"/"时,执行下方的函数
    return {"message": "Hello World"}




#访问fastapi文档
# 1. 访问http://127.0.0.1:8000/docs
# 2. 访问http://127.0.0.1:8000/redoc

#路由
# 1. 路由是指根据请求的URL路径和HTTP方法，将请求分发到对应的处理函数的过程。
# 2. 在FastAPI中，路由是通过装饰器来定义的，例如@app.get("/hello")。
# 3. 路由可以有多个处理函数，例如@app.get("/hello")和@app.post("/hello")。
# 4. 路由可以有多个参数，例如@app.get("/items/{item_id}")。
# 5. 路由可以有多个查询参数，例如@app.get("/items/{item_id}?sort=asc")。
@app.get("/hello")
async def get_hello():
    return {"message":"hello fastapi"}


#练习
# 1. 定义一个路由"/user/hello"，当访问该路由时，返回{"message":"shir"}。
@app.get("/user/hello")
async def learn():
    return {"message":"shir"}



#参数有路径参数，查询参数，请求体参数
# 1. 路径参数是指在URL路径中定义的参数，例如@app.get("/items/{item_id}")中的item_id。
# 2. 查询参数是指在URL路径中定义的参数，例如@app.get("/items/{item_id}?sort=asc")中的sort。
# 3. 请求体参数是指在请求体中定义的参数，例如@app.post("/items/")中的item。



#1. 路径参数
#路径参数的作用是从URL路径中提取参数值，例如@app.get("/items/{item_id}")中的item_id。标识特定资源
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id,"name": f"普通用户{item_id}"}



#限制参数的范围
# 1. 可以使用Python的类型提示来限制参数的范围，例如item_id: int = Path(..., title="The ID of the item to get")。gt/ge(大于/大于等于)，lt/le(小于/小于等于)
# 2. 可以使用Python的类型提示来限制参数的范围，例如sort: str = Query(..., title="Sort by field", description="Sort by field name")。
# 3. 可以使用Python的类型提示来限制参数的范围，例如item: Item = Body(..., title="The item to create")。


'''
string:
max_length: 最大长度
min_length: 最小长度
'''
@app.get("/item/{id}")
async def read_item(id: str=Path(...,min_length=0,max_length=10,description="用户id,范围1-10")):
    return {"item_id": id,"name": f"普通用户{id}"}


'''
2. 查询参数
查询参数不需要路径参数
查询参数的作用是过滤/排序/分页
http://127.0.0.1:8000/news/new_list?skip=6&limit=10中的skip=6,limit=10就是查询参数,中间用&隔开
skip: 跳过的数量，默认值为0
limit: 返回的数量，默认值为10
'''
@app.get("news/new_list")
async def get_new_list(
    skip: int = Query(0,description="跳过的数量"),#Query可以加默认值
    limit: int = Query(10,description="返回的数量")
    ):
    return {"skip": skip,"limit": limit}

#练习
@app.get("/books/check")
async def check_book(
    sort:str=Query("Python开发",min_length=5,max_length=255,description="排序字段5-255"),
    price:int=Query(50,gt=0,lt=100,description="价格范围50-100")
    ):
    return {"sort": sort,"price": price}

#3.请求体参数
#请求体参数的作用创建/更新数据，自动进行数据验证（通过 Pydantic）,数据不在 URL 中（更安全）
#注册用户：用户名和密码
class User(BaseModel):
    username:str=Field("诗人",min_length=2,max_length=10,description="用户名2-10个字符")
    password:str=Field("123456",min_length=6,max_length=20,description="密码6-20个字符")
    
#post方法用来向服务器提交数据，例如注册用户、提交表单等。
@app.post("/user/register")
async def register_user(user:User):
    return {"username": user.username,"password": user.password}


'''
#响应类型有（返回响应对象）：
1. JSON 响应：默认响应类型，用于返回 JSON 数据.示例：return {"message": "Hello World"}
2. HTML 响应：用于返回 HTML 内容.示例：return "<h1>Hello World</h1>"
3. 文本响应：用于返回纯文本内容.示例：return "Hello World"
4. 文件响应：用于返回文件内容.示例：return FileResponse("path/to/file.pdf")
5. 流响应：用于返回流式数据.示例：return StreamingResponse(iter(["Hello World"]))
'''
#fastapi类型默认为JSON响应

@app.get("/html",response_class=HTMLResponse)
async def get_html():
    return "<h1>Hello World</h1>"


#自定义响应数据类型
class News(BaseModel):
    id: int
    content: str
    author: str
#无法更改响应数据类型，只能返回定义的模型
@app.get("/news/{id}",response_model=News)
async def get_news(id: int,content: str,author: str):
    return {"id": id,"content": content,"author": author}


'''
中间件
中间件的作用是在请求处理过程中执行一些操作，例如日志记录、性能监控、身份验证等。（global）
中间件是在请求处理过程中执行的函数，例如日志记录、性能监控、身份验证等。
可以在 FastAPI 中添加中间件，例如：
执行顺序:自下而上
'''
@app.middleware("http")
async def log_request(request,call_next):
    print("中间件1——start")
    response = await call_next(request)
    print("中间件1——end")
    return response

@app.get("/")
async def index():
    return {"message": "Hello World"}


'''
依赖注入
给特定对象添加依赖注入
依赖注入的作用是在请求处理过程中注入一些对象，例如数据库连接、配置信息等。
可以在 FastAPI 中添加依赖注入，例如：
'''

#分页参数逻辑公用
async def pagination(
    skip: int = Query(0,description="跳过的数量"),#Query可以加默认值
    limit: int = Query(10,description="返回的数量")
    ):
    return {"skip": skip,"limit": limit}

@app.get("/news_list")
async def get_news_list(
    commons = Depends(pagination)
    ):
    return commons


@app.get("/user_list")
async def user_list(
    commons = Depends(pagination) 
):
    return commons
