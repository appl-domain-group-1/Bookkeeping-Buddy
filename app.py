from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/login')
def login_page():
    x = 5
    y = 6
    z = x + y
    return render_template("login_test.html", z=z)


if __name__ == '__main__':
    app.run()
