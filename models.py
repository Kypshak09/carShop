from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    rent = db.Column(db.String)

    def __repr__(self):
        return '<User %r>' % self.username

class Car(db.Model):
    __tablename__ = "car"

    id = db.Column(db.Integer, primary_key=True, nullable = False)
    car_id = db.Column(db.String, unique=True, nullable=False)
    car_name = db.Column(db.String, nullable=False)
    description = db.Column(db.String(300), nullable=False)
    price = db.Column(db.String, default=False)
    img = db.Column(db.String)


    def json(self):
        return {'id': self.id, 'car_id': self.car_id,
                'car_name': self.car_name, 'description': self.description, 'price': self.price, 'img': self.img}
    def get_all_cars():
        return [Car.json(movie) for movie in Car.query.all()]

    def add_car(_car_id, _car_name, _description, _price, _img):

        # creating an instance of our Movie constructor
        new_car = Car(car_id=_car_id, car_name=_car_name, description=_description, price=_price, img=_img)
        db.session.add(new_car)
        db.session.commit()


    def get_car(_id):
        return [Car.json(Car.query.filter_by(id=_id).first())]

    def update_car(_id, _car_id, _car_name, _description, _price):

        car_update_to = Car.query.filter_by(id=_id).first()
        car_update_to.car_id = _car_id
        car_update_to.car_name = _car_name
        db.session.commit()

    def delete_car(_id):

        Car.query.filter_by(id=_id).delete()
        # filter movie by id and delete
        db.session.commit()  # commiting the new change to our database