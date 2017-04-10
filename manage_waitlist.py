import requests
from flask_app import db, Hacker, send_email, gen_new_auto_promote_keys
from config_hacktcnj import WAITLIST_LIMIT

num_attendees = db.session.query(Hacker).filter(Hacker.waitlisted == False).count()
num_waitlisted = db.session.query(Hacker).filter(Hacker.waitlisted == True).count()
num_to_promote = WAITLIST_LIMIT - num_attendees

if num_to_promote > num_waitlisted:
    num_to_promote = num_waitlisted

num_to_promote_copy = num_to_promote
num_promoted = 0
errs = []

mlh_ids = db.session.query(Hacker.mlh_id).filter(Hacker.waitlisted == True).order_by(Hacker.registration_time)

for id in mlh_ids:
    if num_to_promote > 0:
        print('Attempting to promote: ' + str(id[0]))
        (key, val) = gen_new_auto_promote_keys()
        url = 'http://hacktcnj.com/promote_from_waitlist' + '?mlh_id=' + str(id[0]) + '&' + key + '=' + val
        req = requests.get(url)
        if req.status_code == 500:
            errs.append('Server 500')
        if not req.status_code == 200 or not req.json()['status'] == 'success':
            errs.append(req.json())

        num_promoted += 1
        num_to_promote -= 1
    else:
        break

print('\n')

msg = 'Hi, here is your daily waitlist report:\n'
msg += '\nBefore Promotion:\n'
msg += '  Reg Cap:        ' + str(WAITLIST_LIMIT) + '\n'
msg += '  Num Attendees:  ' + str(num_attendees) + '\n'
msg += '  Num Waitlisted: ' + str(num_waitlisted) + '\n'
msg += '  Num to Promote: ' + str(num_to_promote_copy) + '\n'
msg += '\nAfter Promotion:\n'
msg += '  Num Promoted (Attempted): ' + str(num_promoted) + '\n'
msg += '  Error Count:              ' + str(len(errs)) + '\n'
msg += '  Num To Promote:           ' + str(num_to_promote) + '\n'
msg += '\nPromotion Error Messages:\n'
msg += '  ' + str(errs) + '\n'

print(msg)

send_email('acm@tcnj.edu', 'HackTCNJ - Daily Waitlist Report!', msg)
send_email('bohinsk1@tcnj.edu', 'HackTCNJ - Daily Waitlist Report!', msg)
