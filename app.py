from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html') #change the file to its destination file

@app.route('/inventory')
def inventory():
    return render_template('index.html') #change the file to its destination file

@app.route('/audit')
def audit():
    return render_template('index.html') #change the file to its destination file

@app.route('/history')
def history():  
    return render_template('history.html')

if __name__ == '__main__':
    app.run(debug=True)
