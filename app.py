from flask import Flask, render_template, request, Response, redirect, url_for, jsonify, flash, send_file, make_response
from pymongo import MongoClient
import pymongo
from bson.objectid import ObjectId
from datetime import datetime
from models import db1, User, ROLE
import mimetypes
from functools import reduce
from bson.objectid import ObjectId
import mimetypes
import json
import os
from service import login_decorator, admin_decorator
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysecretkey"
client = MongoClient('mongodb://192.168.0.4:27017/')
db = client['mydatabase']

#app1 = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "my_secret_key")
db1.init_app(app)


def process_form():
    summon_res_ids_json = request.form.get('summon_res_id')
    summon_res_ids = json.loads(summon_res_ids_json)
    # process the summon_res_ids list as needed
    return jsonify({'success': True})


@app.route('/', methods=['POST', 'GET'])
def login():
    message = None
    try:
        if request.method == 'POST':
            requested_data = request.form
            email = requested_data['email']
            password = requested_data['password']
            print("hi")
            user = User.query.filter_by(email=email).first()
            print("hello")
            if user:
                if user.check_password(password):
                    if user.role == ROLE.ADMIN:
                        session['role'] = ROLE.ADMIN
                    session['email'] = email
                    # make a log everytime user login to the system
                    #create_log(email)
                    return redirect(url_for('index'))
                else:
                    message = 'Incorrect Credentials Please Try Again!!'
                    return render_template('login.html', messages=message)
            else:
                message = 'User Does not Exist'
                return render_template('login.html', messages=message)
        else:
            return render_template('login.html', messages=message)
    except Exception as e:
        print(f"Error occurred: {e}")
        message = 'An error occurred. Please try again later.'
        return render_template('login.html', messages=message)


with app.app_context():
    db1.create_all()

@app.route("/check_data", methods=["POST"])
def check_data():
    data = request.get_json()
    input_data = data["inputData"]
    result = db.ccps.find_one({"ncrp": input_data})
    if result:
        data_exists = True
    else:
        data_exists = False
    return jsonify({"dataExists": data_exists})


@app.route("/form")
@login_decorator
def form():
    return render_template("insert.html")

@app.route('/register-user', methods=['POST', 'GET'])
@admin_decorator
def register_user():
    try:
        if request.method == 'POST':
            requested_data = request.form
            email = requested_data['email']
            password = requested_data['password']
            first_name = requested_data['first_name']
            last_name = requested_data['last_name']
            role = requested_data['role']

            print(email, password, first_name, last_name, role)

            user = User(email=email, password=password,
                        first_name=first_name, last_name=last_name, role=role)
            user.save()
            return redirect(url_for('all_users'))
        else:
            return render_template('register.html')
    except Exception as e:
        print(f"Error occurred: {e}")
        message = 'An error occurred. Please try again later.'
        return render_template('register.html', messages=message)


@app.route('/users')
@admin_decorator
def all_users():
    try:
        users = User.query.all()
        return render_template('table.html', data=users)
    except Exception as e:
        print(f"Error occurred: {e}")
        message = 'An error occurred. Please try again later.'
        return render_template('table.html', messages=message)


@app.route('/edit-user/<int:id>', methods=['POST', 'GET'])
@admin_decorator
def edit_user(id):
    try:
        if request.method == 'POST':
            requested_data = request.form
            email = requested_data['email']
            password = requested_data['password']
            first_name = requested_data['first_name']
            last_name = requested_data['last_name']
            role = requested_data['role']

            user = User.query.filter_by(id=id).first()
            user.email = email
            user.password_hash = generate_password_hash(password)
            user.first_name = first_name
            user.last_name = last_name
            user.role = role
            user.update()
            return redirect(url_for('all_users'))
        else:
            user = User.query.filter_by(id=id).first()
            return render_template('edit_log.html', data=user)

    except Exception as e:
        print(f"Error occurred: {e}")
        message = 'An error occurred. Please try again later.'
        return render_template('edit.html', messages=message)

@app.route('/delete-user/<int:id>', methods=['POST', 'GET'])
@admin_decorator
def delete_user(id):
    try:
        message = None
        user = User.query.filter_by(id=id).first()
        print(user)
        if user:
            if user.role == ROLE.ADMIN:
                message = 'Cannot delete admin user'
                raise Exception(message)
            else:
                user.delete()
        return redirect(url_for('all_users'))
    except Exception as e:
        print(f"Error occurred: {e}")
        message = 'An error occurred. Please try again later.'
        return redirect(url_for('all_users'), messages=message)


@app.route("/index")
@login_decorator
def index():
    collection = db['ccps']
    data = list(collection.find().sort('_id', pymongo.DESCENDING))
    for i in range(len(data)):
        print(data[i]['ncrp'])
    return render_template("home.html", data=data)


@app.route("/view/<ncrp>")
@login_decorator
def view(ncrp):
    ccpsdata = db.ccps.find_one({'ncrp': ncrp})
    suspect_numbers = ccpsdata['suspect_numbers'][0]
    victim_numbers = ccpsdata['victim_numbers'][0]
    values_to_replace = ["]", "[", '"']
    suspect_numbers = reduce(lambda s, value: s.replace(
        value, ""), values_to_replace, suspect_numbers)
    victim_numbers = reduce(lambda s, value: s.replace(
        value, ""), values_to_replace, victim_numbers)

    # to account data
    tadata = db.ta.find({'ncrp': ncrp})
    cafdata = db.caf.find({'ncrp': ncrp})
    cdrdata = db.cdr.find({'ncrp': ncrp})

    fadata = list(db.fa.find({'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    summondata = list(db.summon_req.find(
        {'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    transdata = list(db.transactions.find(
        {'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    summon_responses = list(db.summon_response.find(
        {'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    result = db.summon_req.find({'ncrp': ncrp}).sort('_id', -1).limit(1)
    maxvalue = result[0]['summon_id']
    result1 = db.fa.find({'ncrp': ncrp}).sort('_id', -1).limit(1)
    max_fa_label = result1[0]['fa_label']
    return render_template("view.html", falength=int(max_fa_label[-1])+1, ccpsdata=ccpsdata, suspect_numbers=suspect_numbers.split(','), victim_numbers=victim_numbers.split(','), summonlength=int(maxvalue[-1])+1, tadata=tadata, summon_responses=summon_responses, cafdata=cafdata, cdrdata=cdrdata, fadata=fadata, summondata=summondata, transdata=transdata)


@app.route('/caffile/<ncrp>/<file_id>')
def get_caf(ncrp, file_id):
    cafdata = db.caf.find({'ncrp': ncrp})
    file_data = None
    for caf in cafdata:
        print(str(caf['_id']) == str(file_id))
        if str(caf['_id']) == file_id:
            attachment_filename = caf['filename']
            file_data = caf['data']
    print(file_data)
    if file_data:
        mime_type, _ = mimetypes.guess_type(attachment_filename)
        if mime_type and mime_type.startswith(('image/', 'application/pdf')):
            # If it's an image file, display the image directly
            response = make_response(file_data)
            # Adjust the content type based on the file type
            response.headers['Content-Type'] = mime_type
            return response
        else:
            # For other file types, trigger a download
            response = make_response(file_data)
            response.headers['Content-Disposition'] = f'attachment; filename={attachment_filename}'
            return response
    else:
        return 'File not found!'


@app.route('/cdrfile/<ncrp>/<file_id>')
def get_cdr(ncrp, file_id):
    cdrdata = db.cdr.find({'ncrp': ncrp})
    file_data = None
    for cdr in cdrdata:
        print(str(cdr['_id']) == str(file_id))
        if str(cdr['_id']) == file_id:
            attachment_filename = cdr['filename']
            file_data = cdr['data']
    if file_data:
        mime_type, _ = mimetypes.guess_type(attachment_filename)
        if mime_type and mime_type.startswith(('image/', 'application/pdf')):
            # If it's an image file, display the image directly
            response = make_response(file_data)
            # Adjust the content type based on the file type
            response.headers['Content-Type'] = mime_type
            return response
        else:
            # For other file types, trigger a download
            response = make_response(file_data)
            response.headers['Content-Disposition'] = f'attachment; filename={attachment_filename}'
            return response
    else:
        return 'File not found!'


@app.route('/get_summonrequest/<ncrp>/<file_id>')
def get_summonrequest(ncrp, file_id):
    summondata = list(db.summon_req.find(
        {'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    file_data = None
    for req in summondata:
        print(str(req['_id']) == str(file_id))
        if str(req['_id']) == file_id:
            attachment_filename = req['summon_filename']
            file_data = req['summon_data']
    if file_data:
        mime_type, _ = mimetypes.guess_type(attachment_filename)
        if mime_type and mime_type.startswith(('image/', 'application/pdf')):
            # If it's an image file, display the image directly
            response = make_response(file_data)
            # Adjust the content type based on the file type
            response.headers['Content-Type'] = mime_type
            return response
        else:
            # For other file types, trigger a download
            response = make_response(file_data)
            response.headers['Content-Disposition'] = f'attachment; filename={attachment_filename}'
            return response
    else:
        return 'File not found!'


@app.route('/get_summonresponse/<ncrp>/<file_id>')
def get_summonresponse(ncrp, file_id):
    summondata = list(db.summon_response.find(
        {'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    file_data = None
    for req in summondata:
        print(str(req['_id']) == str(file_id))
        if str(req['_id']) == file_id:
            attachment_filename = req['summon_filename']
            file_data = req['summon_data']
    if file_data:
        mime_type, _ = mimetypes.guess_type(attachment_filename)
        if mime_type and mime_type.startswith(('image/', 'application/pdf')):
            # If it's an image file, display the image directly
            response = make_response(file_data)
            # Adjust the content type based on the file type
            response.headers['Content-Type'] = mime_type
            return response
        else:
            # For other file types, trigger a download
            response = make_response(file_data)
            response.headers['Content-Disposition'] = f'attachment; filename={attachment_filename}'
            return response
    else:
        return 'File not found!'


@app.route("/edit")
def edit():
    return render_template("editpage.html")


@app.route('/deletevalues/<ncrp>', methods=['POST', 'GET'])
@login_decorator
def deletevalues(ncrp):
    db.ccps.delete_one({'ncrp': ncrp})
    db.cdr.delete_many({'ncrp': ncrp})
    db.caf.delete_many({'ncrp': ncrp})
    db.fa.delete_many({'ncrp': ncrp})
    db.ta.delete_many({'ncrp': ncrp})
    db.summon_req.delete_many({'ncrp': ncrp})
    db.summon_response.delete_many({'ncrp': ncrp})
    print('deleted: ', ncrp)
    return redirect(url_for('index'))


@app.route("/editvalues/<ncrp>", methods=['GET', 'POST'])
@login_decorator
def editvalues(ncrp):
    # ncrp = request.form.get('ncrp')
    print(ncrp)
    ccpsdata = db.ccps.find_one({'ncrp': ncrp})
    suspect_numbers = ccpsdata['suspect_numbers'][0]
    victim_numbers = ccpsdata['victim_numbers'][0]
    values_to_replace = ["]", "[", '"']
    suspect_numbers = reduce(lambda s, value: s.replace(
        value, ""), values_to_replace, suspect_numbers)
    victim_numbers = reduce(lambda s, value: s.replace(
        value, ""), values_to_replace, victim_numbers)

    # to account data
    tadata = db.ta.find({'ncrp': ncrp})
    cafdata = db.caf.find({'ncrp': ncrp})
    cdrdata = db.cdr.find({'ncrp': ncrp})
    fadata = list(db.fa.find({'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    summondata = list(db.summon_req.find(
        {'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    transdata = list(db.transactions.find(
        {'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    summon_responses = list(db.summon_response.find(
        {'ncrp': ncrp}).sort('_id', pymongo.ASCENDING))
    result = db.summon_req.find({'ncrp': ncrp}).sort('_id', -1).limit(1)
    maxvalue = result[0]['summon_id']
    result1 = db.fa.find({'ncrp': ncrp}).sort('_id', -1).limit(1)
    max_fa_label = result1[0]['fa_label']
    return render_template("edit.html", falength=int(max_fa_label[-1])+1, ccpsdata=ccpsdata, suspect_numbers=suspect_numbers.split(','), victim_numbers=victim_numbers.split(','), summonlength=int(maxvalue[-1])+1, tadata=tadata, summon_responses=summon_responses, cafdata=cafdata, cdrdata=cdrdata, fadata=fadata, summondata=summondata, transdata=transdata)


@app.route('/upload', methods=['POST'])
def upload():
    ncrp = request.form.get('ncrp')
    io = request.form.get('io')
    result = request.form.get('resval')
    fraud = request.form.get('type_of_fraud')
    date_offence = request.form.get('date_offence')
    date_report = request.form.get('date_report')
    property_lost = request.form.get('property_lost')
    property_held = request.form.get('property_held')
    property_recovered = request.form.get("property_recovered")
    suspect_numbers = request.form.getlist('suspectNumbers')
    victim_numbers = request.form.getlist('victimNumbers')

    if (str(result) == "valid"):

        if date_offence is None:
            # Set date_offence to current date
            date_offence = datetime.now().strftime('%Y-%m-%d')

        if date_report is None:
            # Set date_offence to current date
            date_report = datetime.now().strftime('%Y-%m-%d')

        cdr_numbers = request.form.getlist('cdr_numbers[]')
        cdr_files = request.files.getlist('cdr_files[]')
        caf_numbers = request.form.getlist('caf_numbers[]')
        caf_files = request.files.getlist('caf_files[]')
        ta_banknames = request.form.getlist('ta_banknames')
        ta_ifscs = request.form.getlist('ta_ifscs')
        ta_upiids = request.form.getlist('ta_upiids')
        fa_labels = request.form.getlist('fa_label')
        fa_names = request.form.getlist('fa_name')
        fa_ifscs = request.form.getlist('fa_ifsc')
        cardtypes = request.form.getlist('cardtype')
        summon_dates = request.form.getlist('summon_date')
        summon_ids = request.form.getlist('summon_id[]')
        summon_requests = request.files.getlist('summon_request')
        summon_res_ids = request.form.getlist('summon_res_id[]')
        summon_res_files = request.files.getlist('summon_response')
        summon_res_ids = json.loads(summon_res_ids[0])
        ta_banknames = json.loads(ta_banknames[0])
        ta_ifscs = json.loads(ta_ifscs[0])
        ta_upiids = json.loads(ta_upiids[0])

        print("name", len(fa_names))

        for i in range(len(fa_names)-1):
            fa_name = fa_names[i]
            fa_ifsc = fa_ifscs[i]
            cardtype = cardtypes[i]
            fa_label = fa_labels[i]

            # Insert the file data into MongoDB
            db.fa.insert_one({
                'fa_name': fa_name,
                'fa_ifsc': fa_ifsc,
                'fa_label': fa_label,
                'cardtype': cardtype,
                'ncrp': ncrp,
                'category': "fa"
            })

        summon_ids = json.loads(summon_ids[0])
        print(summon_ids)
        for i in range(len(summon_requests)):
            summon_id = summon_ids[i]
            summon_date = summon_dates[i]
            summon_request = summon_requests[i]

            # Insert the file data into MongoDB
            db.summon_req.insert_one({
                'summon_id': summon_id,
                'summon_date': summon_date,
                'summon_filename': summon_request.filename,
                'summon_data': summon_request.read(),
                'ncrp': ncrp,
                'category': "summon"
            })
        print(summon_res_ids)
        for i in range(len(summon_res_files)):
            summon_res_id = summon_res_ids[i]
            summon_res_file = summon_res_files[i]

            # Insert the file data into MongoDB
            db.summon_response.insert_one({
                'summon_id': summon_res_id,
                'summon_filename': summon_res_file.filename,
                'summon_data': summon_res_file.read(),
                'ncrp': ncrp,
                'category': "summon_response"
            })

        fa_upirefs = request.form.getlist('fa_upiref')
        fa_amounts = request.form.getlist('fa_amount')
        fa_bankids = request.form.getlist('tbank_id[]')
        fa_tdates = request.form.getlist('fa_transaction_date')
        print('transactions')
        fa_bankids = json.loads(fa_bankids[0])
        print(fa_bankids)

        for i in range(len(fa_bankids)):
            fa_upiref = fa_upirefs[i]
            fa_amount = fa_amounts[i]
            fa_bankid = fa_bankids[i]
            fa_tdate = fa_tdates[i]
            if fa_tdate is None:
                # Set date_offence to current date
                fa_tdate = datetime.now().strftime('%Y-%m-%d')

            # Insert the file data into MongoDB
            db.transactions.insert_one({
                'fa_upiref': fa_upiref,
                'fa_amount': fa_amount,
                'fa_bankid': fa_bankid,
                'fa_tdate': fa_tdate,
                'ncrp': ncrp,
                'category': "transactions"
            })

        for i in range(len(cdr_numbers)):
            cdr_number = cdr_numbers[i]
            cdr_file = cdr_files[i]

            # Insert the file data into MongoDB
            db.cdr.insert_one({
                'cdr_number': cdr_number,
                'filename': cdr_file.filename,
                'data': cdr_file.read(),
                'ncrp': ncrp,
                'category': "cdr"
            })

        for i in range(len(caf_numbers)):
            caf_number = caf_numbers[i]
            caf_file = caf_files[i]

            # Insert the file data into MongoDB
            db.caf.insert_one({
                'caf_number': caf_number,
                'filename': caf_file.filename,
                'data': caf_file.read(),
                'ncrp': ncrp,
                'category': "caf"
            })

        print("bank")
        print(ta_banknames)
        print(len(ta_banknames))
        for i in range(len(ta_banknames)):
            ta_bankname = ta_banknames[i]
            ta_ifsc = ta_ifscs[i]
            ta_upiid = ta_upiids[i]

            # Insert the file data into MongoDB
            db.ta.insert_one({
                'ta_bankname': ta_bankname,
                'ta_ifsc': ta_ifsc,
                'ta_upiid': ta_upiid,
                'ncrp': ncrp,
                'category': "ta"
            })

        db.ccps.insert_one({
            'ncrp': ncrp,
            'io': io,
            'type_of_fraud': fraud,
            'date_offence': date_offence,
            'date_report': date_report,
            'suspect_numbers': suspect_numbers,
            'victim_numbers': victim_numbers,
            'property_lost': property_lost,
            'property_held': property_held,
            'property_recovered': property_recovered
        })
        return redirect(url_for('index'))

    return "not submitted"


@app.route('/update', methods=['POST'])
def update():
    ncrp = request.form.get('ncrp')
    io = request.form.get('io')
    fraud = request.form.get('type_of_fraud')
    date_offence = request.form.get('date_offence')
    date_report = request.form.get('date_report')
    suspect_numbers = request.form.getlist('suspectNumbers')
    victim_numbers = request.form.getlist('victimNumbers')

    property_lost = request.form.get('property_lost')
    property_held = request.form.get('property_held')
    property_recovered = request.form.get("property_recovered")
    cdr_numbers = request.form.getlist('cdr_numbers[]')
    cdr_files = request.files.getlist('cdr_files[]')
    caf_numbers = request.form.getlist('caf_numbers[]')
    caf_files = request.files.getlist('caf_files[]')
    caf_ids = request.form.getlist('caf_id[]')
    cdr_ids = request.form.getlist('cdr_id[]')
    ta_banknames = request.form.getlist('ta_banknames')
    ta_ifscs = request.form.getlist('ta_ifscs')
    ta_upiids = request.form.getlist('ta_upiids')
    ta_ids = request.form.getlist('ta_id')
    fa_labels = request.form.getlist('fa_label')
    fa_names = request.form.getlist('fa_name')
    fa_ids = request.form.getlist('fa_id[]')
    fa_ifscs = request.form.getlist('fa_ifsc')
    cardtypes = request.form.getlist('cardtype')
    summon_dates = request.form.getlist('summon_date')
    summon_ids = request.form.getlist('summon_id[]')
    s_req_ids = request.form.getlist('s_req_id[]')
    s_res_ids = request.form.getlist('s_res_id[]')
    summon_requests = request.files.getlist('summon_request')
    summon_res_ids = request.form.getlist('summon_res_id[]')
    summon_res_files = request.files.getlist('summon_response')
    summon_res_ids = json.loads(summon_res_ids[0])
    ta_banknames = json.loads(ta_banknames[0])
    fa_upirefs = request.form.getlist('fa_upiref')
    fa_amounts = request.form.getlist('fa_amount')
    fa_bankids = request.form.getlist('tbank_id[]')
    fa_tdates = request.form.getlist('fa_transaction_date')
    trans_ids = request.form.getlist('trans_id[]')
    fa_bankids = json.loads(fa_bankids[0])
    trans_ids = json.loads(trans_ids[0])
    ta_ifscs = json.loads(ta_ifscs[0])
    ta_ids = json.loads(ta_ids[0])
    ta_upiids = json.loads(ta_upiids[0])
    s_res_ids = json.loads(s_res_ids[0])
    caf_ids = json.loads(caf_ids[0])
    cdr_ids = json.loads(cdr_ids[0])
    fa_ids = json.loads(fa_ids[0])

    # check for delete condition
    cdrdata = list(db.cdr.find({'ncrp': ncrp}))
    cdr_map = {value: index for index, value in enumerate(cdr_ids)}
    for i in range(len(cdrdata)):
        if (cdr_map.get(str(cdrdata[i]['_id'])) == None):
            # print(cdr_map.get(cdrdata[i]['_id']))
            db.cdr.delete_one({'_id': ObjectId(cdrdata[i]['_id'])})

    cafdata = list(db.caf.find({'ncrp': ncrp}))
    caf_map = {value: index for index, value in enumerate(caf_ids)}
    for i in range(len(cafdata)):
        if (caf_map.get(str(cafdata[i]['_id'])) == None):
            # print(caf_map.get(cafdata[i]['_id']))
            db.caf.delete_one({'_id': ObjectId(cafdata[i]['_id'])})

    tadata = list(db.ta.find({'ncrp': ncrp}))
    ta_map = {value: index for index, value in enumerate(ta_ids)}
    for i in range(len(tadata)):
        if (ta_map.get(str(tadata[i]['_id'])) == None):
            # print(ta_map.get(tadata[i]['_id']))
            db.ta.delete_one({'_id': ObjectId(tadata[i]['_id'])})

    s_ids = json.loads(summon_ids[0])
    sumdata = list(db.summon_req.find({'ncrp': ncrp}))
    sum_map = {value: index for index, value in enumerate(s_ids)}
    for i in range(len(sumdata)):
        if (sum_map.get(str(sumdata[i]['summon_id'])) == None):
            print(str(sumdata[i]['summon_id']))
            print(sum_map.get(str(sumdata[i]['_id'])))
            sum_id_del = db.summon_req.find_one(
                {'_id': ObjectId(sumdata[i]['_id'])})
            sum_id_to_del = sum_id_del['summon_id']
            print(sum_id_to_del)
            db.summon_response.delete_many(
                {'ncrp': ncrp, 'summon_id': sum_id_to_del})
            db.summon_req.delete_one({'_id': ObjectId(sumdata[i]['_id'])})
# transactions data
    fadata = list(db.fa.find({'ncrp': ncrp}))
    fa_map = {value: index for index, value in enumerate(fa_labels)}
    print(fa_map)
    for i in range(len(fadata)):
        if (fa_map.get(str(fadata[i]['fa_label'])) == None):
            print(str(fadata[i]['fa_label']))
            print(fa_map.get(str(fadata[i]['_id'])))
            fa_id_del = db.fa.find_one({'_id': ObjectId(fadata[i]['_id'])})
            fa_id_to_del = fa_id_del['fa_label']
            print(fa_id_to_del)
            db.transactions.delete_many(
                {'ncrp': ncrp, 'fa_bankid': fa_id_to_del})
            db.fa.delete_one({'_id': ObjectId(fadata[i]['_id'])})

    transdata = list(db.transactions.find({'ncrp': ncrp}))
    trans_map = {value: index for index, value in enumerate(trans_ids)}
    for i in range(len(transdata)):
        if (trans_map.get(str(transdata[i]['_id'])) == None):
            # print(caf_map.get(cafdata[i]['_id']))
            db.transactions.delete_one({'_id': ObjectId(transdata[i]['_id'])})

    summon_responses = list(db.summon_response.find({'ncrp': ncrp}))
    s_res_map = {value: index for index, value in enumerate(s_res_ids)}
    for i in range(len(summon_responses)):
        if (s_res_map.get(str(summon_responses[i]['_id'])) == None):
            # print(caf_map.get(cafdata[i]['_id']))
            db.summon_response.delete_one(
                {'_id': ObjectId(summon_responses[i]['_id'])})

    for i in range(len(fa_names)-1):

        fa_name = fa_names[i]
        fa_ifsc = fa_ifscs[i]
        cardtype = cardtypes[i]
        fa_label = fa_labels[i]
        if (i < len(fa_ids)):
            fa_id = fa_ids[i]

            # Insert the file data into MongoDB
            db.fa.update_one(
                # Filter condition to match the specific document
                {'_id': ObjectId(fa_id)},
                {'$set': {
                    'fa_name': fa_name,
                    'fa_ifsc': fa_ifsc,
                    'fa_label': fa_label,
                    'cardtype': cardtype,
                    'category': 'fa'
                }}
            )
        else:
            db.fa.insert_one({
                'fa_name': fa_name,
                'fa_ifsc': fa_ifsc,
                'fa_label': fa_label,
                'cardtype': cardtype,
                'ncrp': ncrp,
                'category': "fa"
            })

    summon_ids = json.loads(summon_ids[0])
    s_req_ids = json.loads(s_req_ids[0])

    for i in range(len(summon_requests)):
        summon_id = summon_ids[i]
        summon_date = summon_dates[i]
        summon_request = summon_requests[i]
        if (i < len(s_req_ids)):
            s_req_id = s_req_ids[i]

            # Insert the file data into MongoDB
            if (summon_request.filename == ""):
                db.summon_req.update_one(
                    # Filter condition to match the specific document by converting id to ObjectId
                    {'_id': ObjectId(s_req_id)},
                    {'$set': {
                        'summon_id': summon_id,
                        'summon_date': summon_date,
                    }}
                )
            else:
                db.summon_req.update_one(
                    # Filter condition to match the specific document by converting id to ObjectId
                    {'_id': ObjectId(s_req_id)},
                    {'$set': {
                        'summon_id': summon_id,
                        'summon_date': summon_date,
                        'summon_filename': summon_request.filename,
                        'summon_data': summon_request.read(),
                    }}
                )
        else:
            db.summon_req.insert_one({
                'summon_id': summon_id,
                'summon_date': summon_date,
                'summon_filename': summon_request.filename,
                'summon_data': summon_request.read(),
                'ncrp': ncrp,
                'category': "summon"
            })

    for i in range(len(summon_res_files)):
        summon_res_id = summon_res_ids[i]
        summon_res_file = summon_res_files[i]
        if (i < len(s_res_ids)):
            s_res_id = s_res_ids[i]

            if (summon_res_file.filename == ""):
                db.summon_response.update_one(
                    {'_id': ObjectId(s_res_id)},
                    {'$set': {
                        'summon_id': summon_res_id,
                    }})
            else:
                db.summon_response.update_one(
                    {'_id': ObjectId(s_res_id)},
                    {'$set': {
                        'summon_id': summon_res_id,
                        'summon_filename': summon_res_file.filename,
                        'summon_data': summon_res_file.read(),
                        'ncrp': ncrp,
                        'category': "summon_response"
                    }})
        else:
            db.summon_response.insert_one({
                'summon_id': summon_res_id,
                'summon_filename': summon_res_file.filename,
                'summon_data': summon_res_file.read(),
                'ncrp': ncrp,
                'category': "summon_response"
            })

    # print(trans_ids)
    print(fa_bankids)

    for i in range(len(fa_bankids)):
        fa_upiref = fa_upirefs[i]
        fa_amount = fa_amounts[i]
        fa_bankid = fa_bankids[i]
        fa_tdate = fa_tdates[i]
        if (i < len(trans_ids)):
            trans_id = trans_ids[i]

            db.transactions.update_one(
                # Filter condition to match the specific document by converting id to ObjectId
                {'_id': ObjectId(trans_id)},
                {'$set': {
                    'fa_upiref': fa_upiref,
                    'fa_amount': fa_amount,
                    'fa_bankid': fa_bankid,
                    'fa_tdate': fa_tdate,
                    'category': 'transactions'
                }}
            )
        else:
            db.transactions.insert_one({
                'fa_upiref': fa_upiref,
                'fa_amount': fa_amount,
                'fa_bankid': fa_bankid,
                'fa_tdate': fa_tdate,
                'ncrp': ncrp,
                'category': "transactions"
            })

    for i in range(len(cdr_numbers)):
        cdr_number = cdr_numbers[i]
        cdr_file = cdr_files[i]

        if (i < len(cdr_ids)):
            cdr_id = cdr_ids[i]
            if (cdr_file.filename == ""):
                db.cdr.update_one(
                    # Filter condition to match the specific document by converting id to ObjectId
                    {'_id': ObjectId(cdr_id)},
                    {'$set': {
                        'cdr_number': cdr_number,
                    }}
                )
            else:
                db.cdr.update_one(
                    # Filter condition to match the specific document by converting id to ObjectId
                    {'_id': ObjectId(cdr_id)},
                    {'$set': {
                        'cdr_number': cdr_number,
                        'filename': cdr_file.filename,
                        'data': cdr_file.read(),
                        'category': 'cdr'
                    }}
                )
        else:
            db.cdr.insert_one({
                'cdr_number': cdr_number,
                'filename': cdr_file.filename,
                'data': cdr_file.read(),
                'ncrp': ncrp,
                'category': "cdr"
            })

    for i in range(len(caf_numbers)):
        caf_number = caf_numbers[i]
        caf_file = caf_files[i]
        if (i < len(caf_ids)):
            caf_id = caf_ids[i]

            if (caf_file.filename == ""):

                db.caf.update_one(
                    {'_id': ObjectId(caf_id)},
                    {'$set': {
                        'caf_number': caf_number,
                    }}
                )
            else:
                db.caf.update_one(
                    {'_id': ObjectId(caf_id)},
                    {'$set': {
                        'caf_number': caf_number,
                        'filename': caf_file.filename,
                        'data': caf_file.read(),
                        'category': 'caf'
                    }}
                )
        else:
            db.caf.insert_one({
                'caf_number': caf_number,
                'filename': caf_file.filename,
                'data': caf_file.read(),
                'ncrp': ncrp,
                'category': "caf"
            })

    for i in range(len(ta_banknames)):
        ta_bankname = ta_banknames[i]
        ta_ifsc = ta_ifscs[i]
        ta_upiid = ta_upiids[i]

        if (i < len(ta_ids)):
            ta_id = ta_ids[i]
            db.ta.update_one(
                # Filter condition to match the specific document
                {'_id': ObjectId(ta_id)},
                {'$set': {
                    'ta_bankname': ta_bankname,
                    'ta_ifsc': ta_ifsc,
                    'ta_upiid': ta_upiid,
                    'category': 'ta'
                }}
            )
        else:
            db.ta.insert_one({
                'ta_bankname': ta_bankname,
                'ta_ifsc': ta_ifsc,
                'ta_upiid': ta_upiid,
                'ncrp': ncrp,
                'category': "ta"
            })

    db.ccps.update_one(
        {'ncrp': ncrp},  # Filter condition to match the specific document
        {'$set': {
            'io': io,
            'type_of_fraud': fraud,
            'date_offence': date_offence,
            'date_report': date_report,
            'suspect_numbers': suspect_numbers,
            'victim_numbers': victim_numbers,
            'property_lost': property_lost,
            'property_held': property_held,
            'property_recovered': property_recovered
        }}
    )
    return "submitted"


@app.route('/search', methods=['GET', 'POST'])
@login_decorator
def search():
    query = request.args.get('query')
    print(query)
    collection = db['ccps']
    results = collection.find({"ncrp": {"$regex": query, "$options": "i"}})
    print(results)
    return render_template('search.html', data=results)

@app.route('/logout')
@login_decorator
def logout():
    try:
        session.clear()
        return redirect(url_for('login'))
    except Exception as e:
        print(f"Error occurred: {e}")
        message = 'An error occurred. Please try again later.'
        return render_template('login.html', messages=message)


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
