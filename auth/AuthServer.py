from flask import Flask, jsonify
from flask import request

app = Flask(__name__)


def runServer(config, semaphore):
    @app.route('/')
    def helloWorld():
        return 'Hello, World!'

    @app.route('/callback', methods=["GET"])
    def callback():
        authCode = request.args.get("code")
        state = request.args.get("state")
        cookies = request.cookies
        semaphore.put(authCode)
        return "Authorization code acquisition successful"

    @app.route('/shutdown', methods=['GET'])
    def shutdown():
        shutdownServer()
        return 'Server shutting down...'

    def shutdownServer():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
    semaphore.put("ready")
    host, port = config["server_host"], config["server_port"]
    app.run(host=host, port=port, ssl_context='adhoc')
