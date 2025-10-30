# Libraries imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Repository imports
from .router import main_router


app = FastAPI(
    title="Chatbot API", description="API for the Chatbot service", version="1.0.0"
)

# FastAPI setup for CodeServer proxy
# app = FastAPI(  # title and root path to run PORTS proxy
#     title="HelpDesk_Chatbot_BE", root_path="/proxy/40"
# )


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Chatbot API"}


# Include the main router
app.include_router(main_router)


# Server port and uvicorn instantiation
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9001)
