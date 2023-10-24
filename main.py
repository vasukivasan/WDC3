from flask import Flask, request,flash,redirect, url_for
from werkzeug.utils import secure_filename
from service.GaitService import GaitService
from session.azureSession import AzureSession
from session.mongoSession import MongoSession
from ast import literal_eval
import threading
import os


UPLOAD_FOLDER = os.path.join(os.getcwd(),os.path.join('WDC2/data','videos'))
ALLOWED_EXTENSIONS = {'mov', 'mp4','gif'}

app = Flask(__name__,
            static_url_path='/static', 
            static_folder='static',
            template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

azureSession = AzureSession()
mongoSession = MongoSession()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit', methods=['POST'])
def submit():

    if 'file' not in request.files:
        flash('No file part')
        return {'Status':'file not found'}

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        emptyDocId = mongoSession.createDoc()
        service = GaitService(azureSession, mongoSession, file.filename)
        t1 = threading.Thread(target=service.run)
        t1.start()
        return {'Status': 'Success','_id': str(emptyDocId)}
    else:
        return {'Status': 'File format not allowed'}


@app.route('/result', methods=['GET', 'POST'])
def result():

    data =literal_eval( request.data.decode('utf-8'))
    if mongoSession.docIsEmpty(data['_id']):
        return {'Status': 'Processing'}
    doc = mongoSession.getDoc(data['_id']) 
    doc['_id']= data['_id']
    mongoSession.clearSession()

    return {'Status': 'Completed','Document': doc}

@app.route('/', methods=['GET'])
def dummy():
    return {'Status': 'Success'}

if __name__=="__main__":
    app.run(host="0.0.0.0")
