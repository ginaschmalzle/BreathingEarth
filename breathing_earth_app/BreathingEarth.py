from flask import Flask, request, url_for, render_template
app = Flask(__name__)

@app.route("/")
def main():
    return render_template('index.html');

@app.route("/test/")
def testing():
	return "This is a test"

if __name__ == "__main__":
    app.run()
