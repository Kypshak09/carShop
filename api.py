from importlib.resources import Resource

from flask import jsonify, request, Response
from models import Car
from app import create_app,db,login_manager,bcrypt
app = create_app()


@app.route('/cars', methods=['GET'])
def get_cars():
    return jsonify({'Cars': Car.get_all_cars()})

@app.route('/cars/<int:id>', methods=['GET'])
def get_car_by_id(id):
    return_value = Car.get_car(id)
    return jsonify(return_value)

@app.route('/cars', methods=['PATCH'])
def add_car():
    request_data = request.get_json()  # getting data from client
    Car.add_car(request_data["car_name"], request_data["description"],
                request_data["price"])
    response = Response("Movie added", 201)
    return response



@app.route('/cars/<int:id>', methods=['PATCH'])
def update_car(id):
    request_data = request.get_json()
    Car.update_car(id, request_data['car_name'])
    response = Response("Movie Updated", status=200, mimetype='application/json')
    return response

@app.route('/cars/<int:id>', methods=['DELETE'])
def remove_car(id):
    Car.delete_car(id)
    response = Response("Movie Deleted", status=200, mimetype='application/json')
    return response

if __name__ == "__main__":
    app.run(port=1234, debug=True)
