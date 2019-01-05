from flask import Flask, render_template
from flask import request, redirect


app = Flask(__name__)




@app.route('/')
def hello_world():
    author = "Me"
    name = "You"
    return render_template('index.html', author=author, name=name)

@app.route('/signup', methods = ['POST'])
def signup():
    m_hour = request.form['m_hour']
    m_min = request.form['m_min']
    print(m_hour,m_min)
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0')






