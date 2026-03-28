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
from routes.automation_routes import router as automation_router
from routes.claim_routes import router as claim_router
from routes.courier_routes import router as courier_router
from routes.analytics_routes import router as analytics_router
from routes.financial_routes import router as financial_router
from routes.master_sku_routes import router as master_sku_router
from routes.import_routes import router as import_router
from routes.return_routes import router as return_router
from routes.replacement_routes import router as replacement_router
from routes.returns_routes import router as returns_router
from routes.loss_routes import router as loss_router
from routes.edit_history_routes import router as edit_history_router
from routes.channel_routes import router as channel_router
from routes.platform_listing_routes import router as platform_listing_router
from routes.procurement_batch_routes import router as procurement_batch_router
from routes.upload_routes import router as upload_router
from routes.inventory_routes import router as inventory_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title="E-commerce Operations Management", redirect_slashes=False)

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
app.include_router(whatsapp_router, prefix="/api")
app.include_router(automation_router, prefix="/api")
app.include_router(claim_router, prefix="/api")
app.include_router(courier_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(financial_router, prefix="/api")
app.include_router(master_sku_router, prefix="/api")
app.include_router(import_router, prefix="/api")
app.include_router(return_router, prefix="/api")
app.include_router(replacement_router, prefix="/api")
app.include_router(returns_router, prefix="/api")
app.include_router(loss_router, prefix="/api")
app.include_router(edit_history_router, prefix="/api")
app.include_router(channel_router, prefix="/api")
app.include_router(platform_listing_router, prefix="/api")
app.include_router(procurement_batch_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    # Start background automation processor
    import asyncio
    from automation_service import automation_service
    from database import get_database as get_db
    
    async def process_automations_periodically():
        while True:
            try:
                db = await get_db()
                count = await automation_service.process_scheduled_automations(db)
                if count > 0:
                    logger.info(f"Processed {count} scheduled automations")
            except Exception as e:
                logger.error(f"Automation processor error: {e}")
            await asyncio.sleep(300)  # Check every 5 minutes
    
    asyncio.create_task(process_automations_periodically())

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
