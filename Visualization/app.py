# -*- coding: UTF_8 -*-

from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def graphs():
    values = []
    for i in range(1, 10):
        for j in range(1, 101):
            values.append(j)
    return render_template('layout.html', values=values)



if __name__ == '__main__':
    app.run(debug=True, port=8080)
