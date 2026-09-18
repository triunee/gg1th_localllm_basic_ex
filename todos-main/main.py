from fastapi import FastAPI, Form, Request, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uvicorn
from database import Base, SessionLocal, engine
import models

app = FastAPI()

# DB 엔진 연결
# -> models.py에 정의한 클래스(Todo)를 기준으로, 없으면 테이블을 생성함
# -> 이미 테이블이 있으면 아무 동작도 하지 않음 (기존 데이터는 유지)
Base.metadata.create_all(bind=engine)

# 라우트 함수마다 DB 세션을 하나씩 열어주는 의존성(Dependency) 함수
# FastAPI가 Depends(get_db)를 만나면 이 함수를 실행해서 db 세션을 넘겨주고,
# 요청 처리가 끝나면(성공/실패 상관없이) finally에서 세션을 닫아줌
def get_db():
    db = SessionLocal()
    try:
        yield db  # 여기서 반환된 db 세션이 각 라우트 함수의 인자로 주입됨
    except Exception as e :
        print(f"db연결 오류 {e}")
        raise
    finally:
        db.close()

# html 문서를 위한 객체 (templates 폴더 안의 .html 파일을 렌더링할 때 사용)
templates = Jinja2Templates(directory="templates")

# 정적파일을 위한 설정
## 정적파일(static) 종류(image, css, js)
## "/static" 경로로 들어오는 요청을 static 폴더의 실제 파일과 매핑
app.mount("/static", StaticFiles(directory="static"), name="static")

# localhost:8000/
# todo 목록 전체를 조회해서 메인 페이지(index.html)를 보여주는 라우트
@app.get("/")
def home(request: Request, db_ss: Session = Depends(get_db)):
    # db 객체 생성, 세션연결하기 <- 의존성 주임으로 처리
    # 테이블 조회 (최신순 정렬: id 기준 내림차순)
    todos = db_ss.query(models.Todo).order_by(models.Todo.id.desc()).all()

    print(type(todos))
    # db 조회한 결과를 출력함
    # for todo in todos:
    #     print(todo.id, todo.task, todo.completed)

    # index.html 템플릿에 todos 목록을 "todoss"라는 이름으로 전달
    return templates.TemplateResponse(
        request = request,
        name = "index.html",
        context={ "todoss": todos}
        )

# 새로운 todo 항목을 추가하는 라우트 (index.html의 <form action="/add">에서 호출됨)
@app.post("/add")
def add(task: str = Form(...), db_ss: Session = Depends(get_db)):
    # 클라이언트에서 textarea에서 입력 데이터 넘어온것 확인
    print(task)
    # 클라이언트에서 넘어온 task를 Todo 객체로 생성 (completed는 기본값 False)
    todo = models.Todo(task=task)

    # 의존성 주입에서 처리함 Depends(get_db) : 엔진객체생성, 세션연결
    # db 테이블에 task 저장하기
    print(todo)
    db_ss.add(todo)      # 세션에 새 객체 등록 (아직 DB에는 반영 안 됨)
    # db에 실제 저장, commit
    db_ss.commit()        # 실제 DB에 반영(INSERT)
    # 처리 후 목록 페이지(home)로 다시 이동 (새로고침 시 중복 등록 방지를 위해 303 리다이렉트 사용)
    return RedirectResponse(url=app.url_path_for("home"),
                            status_code=status.HTTP_303_SEE_OTHER)

# 문제 : todo 1개 삭제
# 삭제 버튼(form action="/delete/{todo_id}") 클릭 시 호출되는 라우트
@app.post("/delete/{todo_id}")
def delete(todo_id: int, db_ss: Session = Depends(get_db)):
    # URL 경로로 받은 todo_id에 해당하는 todo 1건 조회
    todo = db_ss.query(models.Todo).filter(models.Todo.id == todo_id).first()
    print(todo)
    # 해당 id의 todo가 없으면 404 에러 반환
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db_ss.delete(todo)   # 세션에서 삭제 예약
    db_ss.commit()        # 실제 DB에 반영(DELETE)
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)

# todo 수정을 위한 조회
# 수정 폼(edit.html)을 보여주기 위해 기존 todo 데이터를 조회하는 라우트 (GET)
@app.get("/edit/{todo_id}")
def edit(request: Request, todo_id: int , db_ss: Session = Depends(get_db)):
    # 요청 수정 처리
    todo = db_ss.query(models.Todo).filter(models.Todo.id==todo_id).first()
    print(todo.task)

    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    # edit.html에 기존 todo 데이터를 전달해서 폼에 미리 채워 보여줌
    return templates.TemplateResponse(
        request=request,
        name = "edit.html",
        context = {"todo": todo}
    )

# todo 업데이터 처리
# edit.html 폼 제출 시 실제로 task/completed 값을 수정, 저장하는 라우트 (POST)
@app.post("/edit/{todo_id}")
def update(todo_id: int, task: str = Form(...), completed: bool = Form(False), db: Session = Depends(get_db)):
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    todo.task = task              # 수정된 내용으로 필드 갱신
    todo.completed = completed    # 완료 여부 체크박스 값 반영
    db.commit()                    # 실제 DB에 반영(UPDATE)
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


# python main.py 로 직접 실행할 때만 uvicorn 서버를 띄움
# (다른 모듈에서 import main 할 때는 실행되지 않음)
if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)

# CLI명령 : uvicorn main:app --reload
