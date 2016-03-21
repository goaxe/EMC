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
            nums = [str(random.uniform(10, 20)), str(random.uniform(10, 30))]
            print nums
            redis_store.rpush('k' + port, ','.join(nums))
    return "create data success"


@app.route('/data')
def data():
    ports = ['80', '25', '443', '53', '22', '21', '67', '110', '143', '137', '138', '139', '1024-', '1024+']
    size = []
    count = []
    for port in ports:
        tmp = redis_store.lpop('k' + port)
        if tmp is None:
            size.append(0)
            count.append(0)
        else:
            tmp = tmp.split(',')
            size.append(tmp[0])
            count.append(tmp[1])
    da = {}
    da['size'] = size
    da['count'] = count
    return jsonify(**da)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
