from flask import jsonify, Response

# i think this one is self explanatory lmao

def route() -> tuple[Response, int]:
    return jsonify({"message": "OK"}), 200
