from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from database import connect_to_mongo, close_mongo_connection

from routes.auth_routes import router as auth_router
from routes.order_routes import router as order_router
from routes.task_routes import router as task_router
from routes.dashboard_routes import router as dashboard_router
from routes.product_routes import router as product_router
from routes.user_routes import router as user_router
from routes.whatsapp_routes import router as whatsapp_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title="E-commerce Operations Management")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(product_router, prefix="/api")
app.include_router(user_router, prefix="/api")

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/api")
async def root():
    return {"message": "E-commerce Operations Management API"}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
