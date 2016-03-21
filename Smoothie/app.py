from flask import Flask, render_template, jsonify
from flask.ext.redis import FlaskRedis
import random

REDIS_URL = 'redis://localhost:6379/0'

app = Flask(__name__)
redis_store = FlaskRedis(app)

@app.route('/')
def graph():
    return render_template('show.html', user=redis_store.get('a'))

@app.route('/create_data')
def create_data():
    ports = ['80', '25', '443', '53', '22', '21', '67', '110', '143', '137', '138', '139', '1024-', '1024+']
    for i in range(0, 10):
        for port in ports:
            redis_store.rpush('k' + port, random.uniform(10, 20))
    return "create data success"


@app.route('/data')
def data():
    ports = ['80', '25', '443', '53', '22', '21', '67', '110', '143', '137', '138', '139', '1024-', '1024+']
    data = []
    for port in ports:
        tmp = redis_store.lpop('k' + port)
        if tmp is None:
            tmp = 0
        data.append(tmp)
    da = {}
    da['data'] = data
    return jsonify(**da)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
