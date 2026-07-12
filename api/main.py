# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Note the 'routes.' prefix to match your new file tree!
from routes.ledger import router as ledger_router
from routes.trend import router as trend_router 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach the endpoints to the server
app.include_router(ledger_router)
app.include_router(trend_router)