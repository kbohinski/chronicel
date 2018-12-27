import requests
import time

from config_hackathon import WAITLIST_LIMIT, BASE_URL, UPDATE_EMAILS
from flask_app import db, Hacker, send_email, gen_new_auto_promote_keys, get_mlh_users, AbandonedHacker

num_attendees = db.session.query(Hacker).filter_by(waitlisted=False).count()
num_waitlisted = db.session.query(Hacker).filter_by(waitlisted=True).count()
num_to_promote = WAITLIST_LIMIT - num_attendees

if num_to_promote > num_waitlisted:
    num_to_promote = num_waitlisted

num_to_promote_copy = num_to_promote
num_promoted = 0
errs = []

mlh_ids = db.session.query(Hacker.mlh_id).filter_by(waitlisted=True).order_by(Hacker.registration_time)

for mlh_id in mlh_ids:
    if num_to_promote > 0:
        (key, val) = gen_new_auto_promote_keys()
        url = BASE_URL + 'promote_from_waitlist' + '?mlh_id=' + str(mlh_id[0]) + '&' + key + '=' + val
        req = requests.get(url)
        if req.status_code == 500:
            errs.append('Server 500')
        if not req.status_code == 200 or not req.json()['status'] == 'success':
            errs.append(req.json())
        num_promoted += 1
        num_to_promote -= 1
    else:
        break

abandoned_users = []

result = db.session.query(Hacker)
abandoned_blacklist = db.session.query(AbandonedHacker)
num_abandoned = len(abandoned_blacklist.all())
num_converted = len(abandoned_blacklist.filter(AbandonedHacker.registered == True).all())
for hacker in get_mlh_users():
    obj = result.filter(Hacker.mlh_id == hacker['id']).one_or_none()
    if obj is None:
        if abandoned_blacklist.filter(AbandonedHacker.mlh_id == hacker['id']).one_or_none() is None:
            abandoned_users.append({
                'mlh_id': hacker['id'],
                'email': hacker['email'],
                'first_name': hacker['first_name']
            })

for abandoned in abandoned_users:
    send_email(abandoned['email'], 'reminder', {
        'first_name': abandoned['first_name'],
        'BASE_URL': BASE_URL
    })
    db.session.add(AbandonedHacker(mlh_id=abandoned['mlh_id'], time_email_sent=int(time.time()), registered=False))
    db.session.commit()

for email in UPDATE_EMAILS:
    send_email(email, 'waitlist_report', {
        'WAITLIST_LIMIT': str(WAITLIST_LIMIT),
        'num_attendees': str(num_attendees),
        'num_waitlisted': str(num_waitlisted),
        'num_to_promote_copy': str(num_to_promote_copy),
        'num_promoted': str(num_promoted),
        'errs': errs,
        'num_to_promote': str(num_to_promote),
        'num_abandoned': str(num_abandoned),
        'num_converted': str(num_converted),
        'num_abandoned_sent': str(len(abandoned_users))
    })
