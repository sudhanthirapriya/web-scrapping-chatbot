from flask import request, jsonify
import os

STATIC_API_KEY = os.getenv("API_AUTH_TOKEN")

# Middleware to authenticate using a static key
def auth_middleware(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('Authorization')

        if api_key != STATIC_API_KEY:
            return jsonify({'status': False, 'message': 'Unauthorized access'}), 403

        return func(*args, **kwargs)

    return wrapper
