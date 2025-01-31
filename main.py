from fastapi import FastAPI
from app.routes.user_route import user_router
import uvicorn


#########################
# BLOCK WITH API ROUTES #
#########################

# create instance of the app
app = FastAPI(title="project-lms")

app.include_router(user_router, tags=["users"])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
