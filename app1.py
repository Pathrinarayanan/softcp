from flask import Flask, render_template, request,Response
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import mimetypes
app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']

@app.route("/")
def index():
    
    return render_template("form.html")

@app.route('/upload', methods=['POST'])
def upload():
    ncrp = request.form.get('ncrp')
    io = request.form.get('io')
    fraud = request.form.get('type_of_fraud')
    date_offence = request.form.get('date_offence')
    date_report =request.form.get('date_report')
    suspect_numbers = request.form.getlist('suspectNumbers')
    victim_numbers = request.form.getlist('victimNumbers')
    
    if date_offence is None:
    # Set date_offence to current date
        date_offence = datetime.now().strftime('%Y-%m-%d')

    if date_report is None:
    # Set date_offence to current date
        date_report = datetime.now().strftime('%Y-%m-%d')   
    
    cdr_numbers = request.form.getlist('cdr_numbers[]')
    cdr_files = request.files.getlist('cdr_files[]')
    print(cdr_numbers)
    print(cdr_files)
    
    for i in range(len(cdr_numbers)):
        cdr_number = cdr_numbers[i]
        cdr_file = cdr_files[i]
        
        # Insert the file data into MongoDB
        db.cdr.insert_one({
            'cdr_number': cdr_number,
            'filename': cdr_file.filename,
            'data': cdr_file.read(),
            'ncrp':ncrp,
            'category':"cdr"
        })

    db.ccps.insert_one({
    'ncrp': ncrp,
    'io': io,
    'type_of_fraud': fraud,
    'date_offence': datetime.strptime(date_offence, '%Y-%m-%d'),
    'date_report': datetime.strptime(date_report, '%Y-%m-%d'),
    'suspect_numbers': suspect_numbers,
    'victim_numbers': victim_numbers
})
    return "submitted"





# @app.route('/upload', methods=['POST'])
# def upload():
#     files = request.files.getlist('file[]')
#     for file in files:
#         # Insert the file data into MongoDB
#         db.ccps.insert_one({
#             'filename': file.filename,
#             'data': file.read(),
#             'category': 'cdr_files'
#         })
#     return 'Files successfully uploaded to MongoDB.'

# @app.route('/download/<file_id>')
# def download(file_id):
#     # Find the file in MongoDB using its ObjectId
#     file_data = db.ccps.find_one({'_id': ObjectId(file_id)})
#     if file_data is None:
#         return 'File not found'
    
#     # Return the file data as a Response object
#     return Response(file_data['data'], headers={
#         'Content-Disposition': f'attachment; filename="{file_data["filename"]}"'
#     })

# @app.route('/view/<file_id>')
# def view(file_id):
#     # Find the file in MongoDB using its ObjectId
#     file_data = db.ccps.find_one({'_id': ObjectId(file_id)})
#     if file_data is None:
#         return 'File not found'

#     # Guess the MIME type based on the file extension
#     content_type = mimetypes.guess_type(file_data['filename'])[0]

#     # Return the file data as a Response object with Content-Type header
#     return Response(file_data['data'], headers={
#         'Content-Type': content_type,
#         'Content-Disposition': f'inline; filename="{file_data["filename"]}"'
#     })
if __name__ == '__main__':
    app.run(debug=True)
