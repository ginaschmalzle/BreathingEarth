from flask import Flask, request, url_for, render_template
app = Flask(__name__)

@app.route("/")
def main():
    return render_template('index.html');

@app.route("/Alaska")
def alaska():
    return render_template('Alaska.html');

@app.route("/California")
def california():
    return render_template('California.html');

if __name__ == "__main__":
    app.run()
