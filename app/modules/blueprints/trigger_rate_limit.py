from flask import jsonify, Response

def route() -> tuple[Response, int]:
    return jsonify({"message": "This endpoint can be used to test the rate limiter. It is limited to 1 request per minute."}), 200
