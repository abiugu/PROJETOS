from flask import Flask, render_template
import json

app = Flask(__name__)


@app.route('/')
def index():
    with open('top_odds.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    return render_template('index.html', dados=dados)


if __name__ == "__main__":
    app.run(debug=True)
