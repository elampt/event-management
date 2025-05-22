from fastapi import FastAPI, Request


# Create a FastAPI instance
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}