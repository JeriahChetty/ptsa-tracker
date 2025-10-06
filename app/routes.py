from flask import Flask

app = Flask(__name__)

@app.route('/healthz')
def healthcheck():
    return 'OK', 200

# ...existing code...