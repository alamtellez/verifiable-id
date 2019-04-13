from flask import (Flask, redirect, render_template, request, session, url_for)

app = Flask(__name__, static_url_path='/static')

name = ""
connection = None

@app.route("/", methods=["POST", "GET"])
def index():
    global name
    if request.method == "POST":
        res = request.form["name"]
        if res == "":
            return render_template("index.html", name=None, error="Elige un nombre")
        else:
            name = res
            return render_template("index.html", name=name)

    else:
        if name == "":
            return render_template("index.html", name=None)
        else:
            return render_template("index.html", name=name)

@app.route("/offers", methods=["POST", "GET"])
def offers():
    


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
