from datetime import datetime

API_KEYS = {}

API_KEYS['mailchimp'] = {'user': '',
                         'key': ''}

API_KEYS['pubnub'] = {'pub': '',
                      'sub': '',
                      'channel': 'hacktcnj18-admin'}

API_KEYS['mailgun'] = {'key': '',
                       'url': '',
                       'from': 'HackTCNJ Team <noreply@hacktcnj.com>',
                       'reply_to': 'acm@tcnj.edu'}

API_KEYS['mlh'] = {'client_id': '',
                   'secret': '',
                   'callback': 'https://www.hacktcnj.com/register'}

API_KEYS['mlh']['urls'] = {
    'users': 'https://my.mlh.io/api/v2/users.json?client_id=' + API_KEYS['mlh']['client_id'] + '&secret=' +
             API_KEYS['mlh']['secret'] + '&per_page=9999',
    'auth': 'https://my.mlh.io/oauth/authorize?client_id=' + API_KEYS['mlh']['client_id'] + '&redirect_uri=' +
            API_KEYS['mlh'][
                'callback'] + '&response_type=code&scope=email+phone_number+demographics+birthday+education+event',
    'token': 'https://my.mlh.io/oauth/token?client_id=' + API_KEYS['mlh']['client_id'] + '&client_secret=' +
             API_KEYS['mlh']['secret'] + '&redirect_uri=' + API_KEYS['mlh'][
                 'callback'] + '&grant_type=authorization_code',
    'user': 'https://my.mlh.io/api/v2/user.json'
}

MC_LIST_IDS = {'waitlist': '', 'attending': ''}

WAITLIST_LIMIT = 450
HACKATHON_TIME = datetime.strptime('2018-2-24', '%Y-%m-%d')
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'doc', 'docx', 'rtf']
HACKATHON_NAME = 'HackTCNJ'
TWITTER_LINK = 'http://www.twitter.com/hacktcnj'
BASE_URL = 'https://www.hacktcnj.com/'
UPDATE_EMAILS = ['acm@tcnj.edu', 'goldbes5@tcnj.edu']
WAITLIST_WHITELISTED_EMAIL_DOMAINS = ['tcnj.edu']
EMAIL_SUBJECT_PREFIX = '' + HACKATHON_NAME + ' - '
EMAILS_TO_SUBJECTS = {
    'check_in': 'Thanks for checking in!',
    'goodbye': 'Application dropped',
    'promoted_from_waitlist': 'You\'re In!',
    'welcome': 'Thanks for applying!',
    'waitlist_report': 'Daily Waitlist Report',
    'reminder': 'Complete your application!'
}
