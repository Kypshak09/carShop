import sqlite3

import uvicorn
import secrets
from fastapi import FastAPI
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session
from fastapi.middleware.wsgi import WSGIMiddleware
from typing import List
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
import re
import crud
import models
import schemas

from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
# Init FastAPI
templates = Jinja2Templates(directory="web/templates")
app = FastAPI()
app.mount("/static", StaticFiles(directory="web/static"), name="static")
# Init Flask
flask_app = Flask(__name__,
                  static_url_path='',
                  static_folder='web/static',
                  template_folder='web/templates')

flask_app.config['SECRET_KEY'] = 'my secret key'
# Mount Flask on FastAPI
app.mount("/flask", WSGIMiddleware(flask_app))

# Protect API
security = HTTPBasic()

# Create session
db = SessionLocal()


def fake_hash(password):
    return password + "notreallyhashed"


def get_db_connection():
    conn = sqlite3.connect('fastAPI.db')
    conn.row_factory = sqlite3.Row
    return conn


def current_user_email() -> object:
    user_email = db.info
    if not user_email:
        return None
    return crud.get_user_by_email(db, user_email)


# Only I can use FastAPI functions
def is_current_authenticated(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"madiyar"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"fastapiisthebest"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


'Flask section ----------------------'


@flask_app.route("/register", methods=["GET", "POST"])
def register():
    msg = ''
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        user = crud.get_user_by_email(db, email)
        if user:
            msg = 'Accountz already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not password or not email:
            msg = 'Please fill out the form !'
        elif password != confirm_password:
            msg = 'Passwords do not match !'

        else:
            fake_hashed_password = fake_hash(confirm_password)
            conn = get_db_connection()
            is_active = True

            conn.execute(
                'INSERT INTO users (email, f_name, sr_name, hashed_password, is_active) VALUES (?, ?, ?, ?, ?)',
                (email, first_name, last_name, fake_hashed_password, is_active))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))

    return render_template("register.html", title="Register", msg=msg)


@flask_app.route('/login', methods=["GET", "POST"])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        user = crud.get_user_by_email(db, email)
        password = fake_hash(password)
        if user is None:
            msg = 'Account does not exist'
        elif user.email == email and user.hashed_password == password:
            msg = 'Logged in successfully !'
            db.info = email
            session['authenticated'] = True
            return redirect(url_for('profile'))
        else:
            msg = 'Invalid email address or password!'
    return render_template('login.html', title="Login", msg=msg)


@flask_app.route('/profile')
def profile():
    user = current_user_email()
    if user is None:
        return render_template('403.html')
    return render_template('profile.html', title="Profile", user=user)


@flask_app.route('/about')
def about_page():
    return render_template('about.html', title="About me")


@flask_app.route('/cv', methods=["GET", "POST"])
def cv_upload():
    if current_user_email() is None:
        return redirect(url_for('login'))
    if request.method == "POST":
        f = request.files["file_to_save"]
        f.save(f"saved files/{secure_filename(f.filename)}")

    return render_template('cv.html', title="CV upload")


@flask_app.route("/logout")
def logout():
    session.pop('authenticated', None)
    db.info = None
    return redirect(url_for('about_page'))


'FastAPI section ----------------------'


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, has_access: bool = Depends(is_current_authenticated)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, has_access: bool = Depends(is_current_authenticated)):
    db_user = crud.get_user(db, user_id=user_id)

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user(db=db, db_user=db_user, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, has_access: bool = Depends(is_current_authenticated)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    raise HTTPException(status_code=200, detail="User successfully deleted")


@app.post("/users/{user_id}/projects/", response_model=schemas.Project)
def create_project_for_user(
        user_id: int, project: schemas.ProjectCreate, has_access: bool = Depends(is_current_authenticated)
):
    return crud.create_user_project(db=db, project=project, user_id=user_id)


@app.put("/users/{user_id}/projects/", response_model=schemas.Project)
def update_project_for_user(
        project_id: int, project: schemas.ProjectUpdate, has_access: bool = Depends(is_current_authenticated)
):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.update_user_project(db=db, project=project, db_project=db_project)


@app.get("/projects/{project_id}", response_model=schemas.Project)
def read_project(project_id: int):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@app.get("/projects/", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100):
    projects = crud.get_projects(db, skip=skip, limit=limit)
    return projects


@app.delete("/users/{user_id}/projects/", response_model=schemas.Project)
def delete_project(project_id: int, has_access: bool = Depends(is_current_authenticated)):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(db_project)
    db.commit()
    raise HTTPException(status_code=200, detail="Project successfully deleted")


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)
