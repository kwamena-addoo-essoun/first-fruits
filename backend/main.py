from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import users, clients, projects, timelog, invoices, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Freelancer Time Tracker API",
    description="Time tracking and invoice generation for freelancers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(clients.router, prefix="/api/clients", tags=["clients"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(timelog.router, prefix="/api/timelog", tags=["timelog"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["invoices"])

@app.get("/")
def read_root():
    return {"message": "Freelancer Time Tracker API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
