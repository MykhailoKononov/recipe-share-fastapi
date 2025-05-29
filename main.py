import uvicorn

from fastapi import FastAPI

from app.routes.moderator_route import moderator_router
from app.routes.user_route import user_router, auth_router
from app.routes.recipe_route import recipe_router
from app.routes.admin_route import admin_router

#########################
# BLOCK WITH API ROUTES #
#########################

# create instance of the app
app = FastAPI(title="project-lms")

app.include_router(user_router, prefix="/user")
app.include_router(auth_router, prefix="/auth")
app.include_router(recipe_router, prefix="/recipes")
app.include_router(moderator_router, prefix="/moderator")
app.include_router(admin_router, prefix="/admin")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
