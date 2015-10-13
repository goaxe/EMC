# -*- coding: UTF_8 -*-

from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def graphs():
    return render_template('layout.html')



if __name__ == '__main__':
    app.run(debug=True, port=8080)
