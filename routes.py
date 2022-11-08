import os
import sqlite3

from authlib.integrations.flask_client import OAuth
from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    session, request, abort
)

from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)
from werkzeug.utils import secure_filename

from app import create_app,db,login_manager,bcrypt
from models import User
from forms import login_form,register_form


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)



@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for('list'))
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )



# Register route
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data

            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
            )

            db.session.add(newuser)
            db.session.commit()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account"
        )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

oauth = OAuth(app)

@login_required
@app.route('/auth')
def profile():
    return render_template("profile.html")

# CRUD


@app.route('/createcar/', methods=('GET', 'POST'))
def createcar():
    if request.method == 'POST':
        car_name = request.form['car_name']
        car_id = request.form['car_id']
        img = request.files['img']
        desc = request.form['description']
        price = request.form['price']
        if not id:
            flash('Title is required!')
        elif not car_name:
            flash('Content is required!')
        else:
            conn = get_db_connection()
            filename = secure_filename(img.filename)
            img.save(os.path.join(app.root_path, 'static/uploads', filename))
            # print('upload_image filename: ' + filename)
            conn.execute('INSERT INTO car (car_id, car_name, img, description, price) VALUES (?,?,?,?,?)',
                         (car_id, car_name, filename, desc, price))
            conn.commit()
            conn.close()
            return redirect(url_for('list'))

    return render_template('createpage.html')

@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)




def get_car(id):
    conn = get_db_connection()
    car = conn.execute('SELECT * FROM car WHERE id = ?',
                       (id,)).fetchone()
    conn.close()
    if car is None:
        abort(404)
    return car

@app.route('/cart/<int:id>')
def rent_car(id):
    car = get_car(id)
    current_user.rent = car['img']
    db.session.commit()
    return redirect(url_for('profile'))



@login_required
@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    car = get_car(id)

    if request.method == 'POST':
        car_id = request.form['car_id']
        car_name = request.form['car_name']
        price = request.form['price']
        desc = request.form['description']
        if not car_id:
            flash('Title is required!')

        elif not car_name:
            flash('Content is required!')

        else:
            conn = get_db_connection()
            conn.execute('UPDATE car SET car_id = ?, car_name = ?, price=?, description=?'
                         ' WHERE id = ?',
                         (car_id, car_name, price,desc,id,))
            conn.commit()
            conn.close()
            return redirect(url_for('list'))

    return render_template('edit.html', car=car)


def get_db_connection():
    conn = sqlite3.connect('instance/database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/<int:id>/delete/', methods=('POST', 'GET'))
def delete(id):
    car = get_car(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM car WHERE id = ?', (id,))
    print("deleted")
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(car['id']))
    return redirect(url_for('list'))


@app.route('/')
def list():  # put application's code here
    conn = get_db_connection()
    cars = conn.execute('SELECT * FROM car').fetchall()
    conn.close()
    return render_template('cars.html', cars=cars)




@app.route('/<int:id>/desc', methods=('POST', 'GET'))
def description(id):
    car = get_car(id)

    return render_template('description.html', car=car)


if __name__ == "__main__":
    app.run(debug=True)
