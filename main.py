from fastapi import FastAPI
from database import Base, engine
from user import router as user_router
from org import router as org_router
from ai_routing import router as ai_router   

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(user_router)
app.include_router(org_router)
app.include_router(ai_router)              