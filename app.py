from flask import Flask
from controller.train_controller import get_document, add_document, disable_document, remove_document
from controller.train_controller import chat_with_llm
from controller.auth_middleware import auth_middleware

app = Flask(__name__)

@app.route('/store/add', methods=['POST'], endpoint="add_document")
@auth_middleware
def add():
    return add_document()

@app.route('/store/get', methods=['POST'], endpoint="get_document")
@auth_middleware
def get():
    return get_document()

@app.route('/store/disable', methods=['POST'], endpoint="disable_document")
@auth_middleware
def disable():
    return disable_document()


@app.route('/store/remove', methods=['POST'], endpoint="remove_document")
@auth_middleware
def remove():
    return remove_document()


@app.route('/store/llm/chat', methods=['POST'], endpoint="chat_with_llm")
@auth_middleware
def llm_chat():
    return chat_with_llm()

if __name__ == '__main__':
    app.run(debug=True)
