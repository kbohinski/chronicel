import hashlib
import jinja2
import json
import os
import random
import requests
import string
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_sslify import SSLify
from mailchimp3 import MailChimp
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from werkzeug.utils import secure_filename

from config_hackathon import API_KEYS, MC_LIST_IDS, TWITTER_LINK, WAITLIST_WHITELISTED_EMAIL_DOMAINS, HACKATHON_TIME, \
    ALLOWED_EXTENSIONS, HACKATHON_NAME, WAITLIST_LIMIT, EMAIL_SUBJECT_PREFIX, EMAILS_TO_SUBJECTS

app = Flask(__name__)
sslify = SSLify(app)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

pnconfig = PNConfiguration()

pnconfig.publish_key = API_KEYS['pubnub']['pub']
pnconfig.subscribe_key = API_KEYS['pubnub']['sub']
pnconfig.ssl = True

pn = PubNub(pnconfig)

mc = MailChimp(API_KEYS['mailchimp']['user'], API_KEYS['mailchimp']['key'])


class Hacker(db.Model):
    __tablename__ = 'hackers'

    mlh_id = db.Column(db.Integer, primary_key=True)
    registration_time = db.Column(db.Integer)
    checked_in = db.Column(db.Boolean)
    minor = db.Column(db.Boolean)
    waitlisted = db.Column(db.Boolean)
    admin = db.Column(db.Boolean)


class AutoPromoteKeys(db.Model):
    __tablename__ = 'AutoPromoteKeys'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(4096))
    val = db.Column(db.String(4096))


class AbandonedHacker(db.Model):
    __tablename__ = 'abandoned_hackers'

    mlh_id = db.Column(db.Integer, primary_key=True)
    time_email_sent = db.Column(db.Integer)
    registered = db.Column(db.Boolean)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # Register a hacker...
        if is_logged_in() and db.session.query(
                db.exists().where(Hacker.mlh_id == session['mymlh']['id'])).scalar():
            # Already logged in, take them to dashboard
            return redirect(url_for('dashboard'))

        if request.args.get('code') is None:
            # Get info from MyMLH
            return redirect(API_KEYS['mlh']['urls']['auth'])

        if is_logged_in():
            return render_template('web/register.html', name=session['mymlh']['first_name'])

        code = request.args.get('code')
        oauth_redirect = requests.post(API_KEYS['mlh']['urls']['token'] + '&code=' + code)

        if oauth_redirect.status_code == 200:
            access_token = json.loads(oauth_redirect.text)['access_token']
            user_info_request = requests.get(API_KEYS['mlh']['urls']['user'] + '?access_token=' + access_token)
            if user_info_request.status_code == 200:
                user = json.loads(user_info_request.text)['data']
                session['mymlh'] = user
                if db.session.query(db.exists().where(Hacker.mlh_id == user['id'])).scalar():
                    # User already exists in db, log them in
                    return redirect(url_for('dashboard'))

                return render_template('web/register.html', name=user['first_name'])

        return redirect(url_for('register'))

    if request.method == 'POST':
        if not is_logged_in() or db.session.query(
                db.exists().where(Hacker.mlh_id == session['mymlh']['id'])).scalar():
            # Request flow == messed up somehow, restart them
            return redirect(url_for('register'))

        if 'resume' not in request.files:
            # No file?
            return redirect(url_for('register'))

        resume = request.files['resume']
        if resume.filename == '':
            # No file selected
            return redirect(url_for('register'))

        if resume and not allowed_file(resume.filename):
            return jsonify(
                {'status': 'error', 'action': 'register',
                 'more_info': 'Invalid file type... Accepted types are txt pdf doc docx and rtf... Press back and try again...'})

        if resume and allowed_file(resume.filename):
            # Good file!
            filename = session['mymlh']['first_name'].lower() + '_' + session['mymlh']['last_name'].lower() + '_' + str(
                session['mymlh']['id']) + '.' + resume.filename.split('.')[-1].lower()
            filename = secure_filename(filename)
            resume.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Determine if minor for legal purposes
            minor = False
            birthday = datetime.strptime(session['mymlh']['date_of_birth'], '%Y-%m-%d')
            if relativedelta(HACKATHON_TIME, birthday).years < 18:
                minor = True

            # Determine if hacker should be placed on waitlist
            waitlist = False
            if db.session.query(Hacker).count() + 1 > WAITLIST_LIMIT and session['mymlh']['email'].split('@')[
                -1] not in WAITLIST_WHITELISTED_EMAIL_DOMAINS:
                waitlist = True

            # Add the user to mailchimp
            email_hash = hashlib.md5(session['mymlh']['email'].lower().encode('utf-8')).hexdigest()
            if waitlist:
                mc.lists.members.create_or_update(MC_LIST_IDS['waitlist'], email_hash, {
                    'email_address': session['mymlh']['email'],
                    'status': 'subscribed',
                    'status_if_new': 'subscribed',
                    'merge_fields': {
                        'FNAME': session['mymlh']['first_name'],
                        'LNAME': session['mymlh']['last_name'],
                    }
                })
            else:
                mc.lists.members.create_or_update(MC_LIST_IDS['attending'], email_hash, {
                    'email_address': session['mymlh']['email'],
                    'status': 'subscribed',
                    'status_if_new': 'subscribed',
                    'merge_fields': {
                        'FNAME': session['mymlh']['first_name'],
                        'LNAME': session['mymlh']['last_name'],
                    }
                })

            # Add the user to the database
            db.session.add(
                Hacker(mlh_id=session['mymlh']['id'], registration_time=int(time.time()),
                       checked_in=False, minor=minor, waitlisted=waitlist, admin=False))
            db.session.commit()

            abandoned = db.session.query(AbandonedHacker).filter(
                AbandonedHacker.mlh_id == session['mymlh']['id']).one_or_none()
            if abandoned is not None:
                abandoned.registered = True
                db.session.commit()

            # Send a welcome email
            send_email(session['mymlh']['email'], 'welcome',
                       {'first_name': session['mymlh']['first_name'], 'waitlist': waitlist, 'minor': minor})

            pn.publish().channel(API_KEYS['pubnub']['channel']).message({'action': 'new_user'}).sync()

            # Finally, send them to their dashboard
            return redirect(url_for('dashboard'))


@app.route('/admin', methods=['GET'])
def admin():
    # Displays total registration information...
    # As Firebase could not be used with MyMLH, use PubNub to simulate the realtime database...
    if not is_admin():
        return redirect(url_for('register'))

    waitlist_count = 0
    total_count = 0
    check_in_count = 0
    admin_count = 0
    shirt_count = {'xxs': 0, 'xs': 0, 's': 0, 'm': 0, 'l': 0, 'xl': 0, 'xxl': 0}
    male_count = 0
    female_count = 0
    non_binary_count = 0
    prefer_not_to_say_count = 0
    other_count = 0
    schools = {}
    majors = {}

    mlh_info = get_mlh_users()

    hackers = []

    result = db.session.query(Hacker)

    for hacker in mlh_info:
        obj = result.filter(Hacker.mlh_id == hacker['id']).one_or_none()

        if obj is None:
            continue

        if obj.waitlisted:
            waitlist_count += 1

        if obj.checked_in:
            check_in_count += 1

        if obj.admin:
            admin_count += 1

        if hacker['gender'] == 'Male':
            male_count += 1
        elif hacker['gender'] == 'Female':
            female_count += 1
        elif hacker['gender'] == 'Non-binary':
            non_binary_count += 1
        elif hacker['gender'] == 'I prefer not to say':
            prefer_not_to_say_count += 1
        else:
            other_count += 1

        total_count += 1

        if hacker['school']['name'] not in schools:
            schools[hacker['school']['name']] = 1
        else:
            schools[hacker['school']['name']] += 1

        if hacker['major'] not in majors:
            majors[hacker['major']] = 1
        else:
            majors[hacker['major']] += 1

        shirt_count[hacker['shirt_size'].split(' - ')[1].lower()] += 1

        hackers.append({
            'checked_in': obj.checked_in,
            'waitlisted': obj.waitlisted,
            'admin': obj.admin,
            'minor': obj.minor,
            'registration_time': obj.registration_time,
            'id': hacker['id'],
            'email': hacker['email'],
            'first_name': hacker['first_name'],
            'last_name': hacker['last_name'],
            'phone_number': hacker['phone_number'],
            'dietary_restrictions': hacker['dietary_restrictions'],
            'special_needs': hacker['special_needs'],
            'school': hacker['school']
        })

    abandoned_users_count = len(mlh_info) - total_count

    return render_template('web/admin.html', hackers=hackers, total_count=total_count, waitlist_count=waitlist_count,
                           check_in_count=check_in_count, admin_count=admin_count, shirt_count=shirt_count,
                           female_count=female_count, male_count=male_count, non_binary_count=non_binary_count,
                           prefer_not_to_say_count=prefer_not_to_say_count, other_count=other_count, schools=schools,
                           majors=majors, abandoned_users_count=abandoned_users_count,
                           mlh_url=API_KEYS['mlh']['urls']['users'])


@app.route('/change_admin', methods=['GET'])
def change_admin():
    # Promote or drop a given hacker to/from admin status...
    if not is_admin():
        return jsonify({'status': 'error', 'action': 'modify_permissions',
                        'more_info': 'You do not have permissions to perform this action...'})

    if request.args.get('mlh_id') is None or request.args.get('action') is None:
        return jsonify({'status': 'error', 'action': 'change_admin', 'more_info': 'Missing required field...'})

    valid_actions = ['promote', 'demote']
    if request.args.get('action') not in valid_actions:
        return jsonify({'status': 'error', 'action': 'change_admin', 'more_info': 'Invalid action...'})

    if request.args.get('action') == 'promote':
        db.session.query(Hacker).filter(Hacker.mlh_id == request.args.get('mlh_id')).update({'admin': True})
    elif request.args.get('action') == 'demote':
        db.session.query(Hacker).filter(Hacker.mlh_id == request.args.get('mlh_id')).update({'admin': False})
    db.session.commit()

    pn.publish().channel(API_KEYS['pubnub']['channel']).message(
        {'status': 'success', 'action': 'change_admin:' + request.args.get('action'), 'more_info': '',
         'id': request.args.get('mlh_id')}).sync()

    return jsonify({'status': 'success', 'action': 'change_admin:' + request.args.get('action'), 'more_info': '',
                    'id': request.args.get('mlh_id')})


@app.route('/check_in', methods=['GET'])
def check_in():
    # Check in a hacker...
    if not is_admin():
        return jsonify({'status': 'error', 'action': 'check_in',
                        'more_info': 'You do not have permissions to perform this action...'})

    if request.args.get('mlh_id') is None:
        return jsonify({'status': 'error', 'action': 'check_in', 'more_info': 'Missing required field...'})

    # See if hacker was already checked in or a minor...
    (checked_in, minor) = db.session.query(Hacker.checked_in, Hacker.minor).filter(
        Hacker.mlh_id == request.args.get('mlh_id')).one_or_none()

    if checked_in:
        return jsonify({'status': 'error', 'action': 'check_in', 'more_info': 'Hacker already checked in!'})

    # Update db...
    db.session.query(Hacker).filter(Hacker.mlh_id == request.args.get('mlh_id')).update({'checked_in': True})
    db.session.commit()

    mlh_info = get_mlh_user(request.args.get('mlh_id'))

    # Send a welcome email...
    send_email(mlh_info['email'], 'check_in', {'first_name': mlh_info['first_name']})

    pn.publish().channel(API_KEYS['pubnub']['channel']).message(
        {'status': 'success', 'action': 'check_in', 'more_info': '', 'minor': minor,
         'id': request.args.get('mlh_id')}).sync()

    return jsonify(
        {'status': 'success', 'action': 'check_in', 'more_info': '', 'minor': minor,
         'id': request.args.get('mlh_id')})


@app.route('/drop', methods=['GET'])
def drop():
    # Drop a hacker's registration...
    if request.args.get('mlh_id') is None:
        return jsonify({'status': 'error', 'action': 'drop', 'more_info': 'Missing required field...'})

    if not is_admin() and not is_self(request.args.get('mlh_id')):
        return jsonify({'status': 'error', 'action': 'drop',
                        'more_info': 'You do not have permissions to perform this action...'})

    row = db.session.query(Hacker.checked_in, Hacker.waitlisted).filter(
        Hacker.mlh_id == request.args.get('mlh_id')).one_or_none()

    if row is None:
        return jsonify({'status': 'error', 'action': 'drop',
                        'more_info': 'Could not find hacker...'})

    (checked_in, waitlisted) = row

    if checked_in:
        return jsonify({'status': 'error', 'action': 'drop', 'more_info': 'Cannot drop, already checked in...'})

    mlh_info = get_mlh_user(request.args.get('mlh_id'))

    # Delete from db...
    row = db.session.query(Hacker).filter(Hacker.mlh_id == request.args.get('mlh_id')).first()
    db.session.delete(row)
    db.session.commit()

    # Delete resume...
    for ext in ALLOWED_EXTENSIONS:
        filename = mlh_info['first_name'].lower() + '_' + mlh_info['last_name'].lower() + '_' + request.args.get(
            'mlh_id') + '.' + ext
        try:
            os.remove(app.config['UPLOAD_FOLDER'] + '/' + filename)
        except OSError:
            pass

    # Delete user from mailchimp...
    email_hash = hashlib.md5(mlh_info['email'].lower().encode('utf-8')).hexdigest()
    if waitlisted:
        mc.lists.members.delete(MC_LIST_IDS['waitlist'], email_hash)
    else:
        mc.lists.members.delete(MC_LIST_IDS['attending'], email_hash)

    # Send a goodbye email...
    send_email(mlh_info['email'], 'goodbye', {'first_name': mlh_info['first_name']})

    pn.publish().channel(API_KEYS['pubnub']['channel']).message(
        {'status': 'success', 'action': 'drop', 'more_info': '', 'id': request.args.get('mlh_id')}).sync()

    if is_self(request.args.get('mlh_id')):
        session.clear()

    return jsonify({'status': 'success', 'action': 'drop', 'more_info': '', 'id': request.args.get('mlh_id')})


@app.route('/promote_from_waitlist', methods=['GET'])
def promote_from_waitlist():
    # Promote a hacker from the waitlist...
    if request.args.get('mlh_id') is None:
        return jsonify(
            {'status': 'error', 'action': 'promote_from_waitlist', 'more_info': 'Missing required field...'})

    (key, val) = get_auto_promote_keys()

    if request.args.get(key) is None:
        if not is_admin():
            return jsonify({'status': 'error', 'action': 'promote_from_waitlist',
                            'more_info': 'You do not have permissions to perform this action...'})
    else:
        if request.args.get(key) != val:
            return jsonify({'status': 'error', 'action': 'promote_from_waitlist',
                            'more_info': 'Invalid auto promote keys...'})

    (checked_in, waitlisted) = db.session.query(Hacker.checked_in, Hacker.waitlisted).filter(
        Hacker.mlh_id == request.args.get('mlh_id')).one_or_none()

    if checked_in:
        return jsonify(
            {'status': 'error', 'action': 'promote_from_waitlist',
             'more_info': 'Cannot promote, already checked in...'})

    if not waitlisted:
        return jsonify(
            {'status': 'error', 'action': 'promote_from_waitlist',
             'more_info': 'Cannot promote, user is not waitlisted...'})

    # Update db...
    db.session.query(Hacker).filter(Hacker.mlh_id == request.args.get('mlh_id')).update({'waitlisted': False})
    db.session.commit()

    mlh_info = get_mlh_user(request.args.get('mlh_id'))

    # Send a welcome email...
    send_email(mlh_info['email'], 'promoted_from_waitlist', {'first_name': mlh_info['first_name']})

    # Swap mailchimp lists...
    email_hash = hashlib.md5(mlh_info['email'].lower().encode('utf-8')).hexdigest()
    mc.lists.members.delete(MC_LIST_IDS['waitlist'], email_hash)
    mc.lists.members.create_or_update(MC_LIST_IDS['attending'], email_hash, {
        'email_address': mlh_info['email'],
        'status': 'subscribed',
        'status_if_new': 'subscribed',
        'merge_fields': {
            'FNAME': mlh_info['first_name'],
            'LNAME': mlh_info['last_name'],
        }
    })

    pn.publish().channel(API_KEYS['pubnub']['channel']).message(
        {'status': 'success', 'action': 'promote_from_waitlist', 'more_info': '',
         'id': request.args.get('mlh_id')}).sync()

    return jsonify(
        {'status': 'success', 'action': 'promote_from_waitlist', 'more_info': '', 'id': request.args.get('mlh_id')})


@app.route('/dashboard', methods=['GET'])
def dashboard():
    # Display's a hacker's options...
    if not is_logged_in():
        return redirect(url_for('register'))

    return render_template('web/dashboard.html', name=session['mymlh']['first_name'], id=session['mymlh']['id'],
                           admin=is_admin())


def is_logged_in():
    if session is None:
        return False
    if 'mymlh' not in session:
        return False
    return True


def is_admin():
    if not is_logged_in():
        return False
    user_admin = db.session.query(Hacker.admin).filter(Hacker.mlh_id == session['mymlh']['id']).one_or_none()
    if user_admin is None:
        return False
    if not user_admin[0]:
        return False
    return True


def is_self(mlh_id):
    mlh_id = int(mlh_id)
    if not is_logged_in():
        return False
    if session['mymlh']['id'] != mlh_id:
        return False
    return True


def send_email(to, tmp, ctx):
    ctx['hackathon_name'] = HACKATHON_NAME
    ctx['twitter_link'] = TWITTER_LINK
    msg = jinja2.Environment(loader=jinja2.FileSystemLoader(
        str(os.path.join(os.path.dirname(os.path.abspath(__file__)))) + '/templates/email/')).get_template(
        tmp + '.txt').render(ctx)
    subject = EMAIL_SUBJECT_PREFIX + EMAILS_TO_SUBJECTS[tmp]
    return requests.post(
        API_KEYS['mailgun']['url'],
        auth=('api', API_KEYS['mailgun']['key']),
        data={'from': API_KEYS['mailgun']['from'],
              'to': [to],
              'subject': subject,
              'text': msg,
              'h:Reply-To': API_KEYS['mailgun']['reply_to']})


def get_mlh_user(mlh_id):
    if not isinstance(mlh_id, int):
        mlh_id = int(mlh_id)
    req = requests.get(API_KEYS['mlh']['urls']['users'])
    if req.status_code == 200:
        hackers = req.json()['data']
        for hacker in hackers:
            if hacker['id'] == mlh_id:
                return hacker


def get_mlh_users():
    req = requests.get(API_KEYS['mlh']['urls']['users'])
    if req.status_code == 200:
        return req.json()['data']


def gen_new_auto_promote_keys(n=50):
    def new_key(n):
        return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(n))

    key = new_key(n)
    val = new_key(n)
    db.session.add(AutoPromoteKeys(key=key, val=val))
    db.session.commit()
    return (key, val)


def get_auto_promote_keys():
    row = db.session.query(AutoPromoteKeys).one_or_none()
    if row is not None:
        db.session.delete(row)
        db.session.commit()
        return (row.key, row.val)
    else:
        return ('', '')


def allowed_file(filename):
    return '.' in filename and \
           filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run()
