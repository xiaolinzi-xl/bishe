from flask import Blueprint
from flask_restful import Api, Resource

chat_bp = Blueprint('chat_bp', __name__)
chat_api = Api(chat_bp)

# your code
