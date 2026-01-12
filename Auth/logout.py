from fastapi import FastAPI, Body, Header, HTTPException, Depends, Request, Form, Response
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates/Auth_forms")

def logout_func(app):
    
    @app.get("/logout")
    def logout(
        request: Request,
        response: Response
    ):
        if "access" in request.cookies:
            response.delete_cookie("access")
        else:
            raise HTTPException(401, "Unauthorized")

        if "refresh" in request.cookies:
            response.delete_cookie("refresh")
        else:
            raise HTTPException(401, "Unauthorized")
        
        return {"msg": "Logout Successful"}