from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from maestro_testing import Controller
import os

app = Flask(__name__)
CORS(app)

tango = Controller(ttyStr='/dev/ttyACM0') 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control():
    data = request.json
    m_type = data.get('type')
    val = int(data.get('value', 6000)) 
    
    if m_type == 'waist': tango.setTarget(0, val)
    elif m_type == 'pan': tango.setTarget(3, val)
    elif m_type == 'tilt': tango.setTarget(4, val)
    elif m_type == 'stop':
        for i in range(6): tango.setTarget(i, 6000)
        tango.setTarget(0, 5600)
        
    return jsonify(status="ok")


@app.route('/drive', methods=['POST'])
def drive():
    data = request.json
    x = int(data.get('x', 6000))
    y = int(data.get('y', 6000))
    print(x, y) 
    tango.drive(x, y) 
    
    return jsonify(status="driving")



@app.route('/speak', methods=['POST'])
def speak():
    data = request.json
    phrase = data.get('phrase')
    
    #voice output
    os.system(f'espeak "{phrase}"')
    return jsonify(status="talking")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
