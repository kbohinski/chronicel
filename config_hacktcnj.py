from datetime import datetime

api_keys = {}

api_keys['mailchimp'] = {'user': '', 'key': ''}

api_keys['pubnub'] = {'pub': '',
                      'sub': ''}

api_keys['mailgun'] = ''

api_keys['mlh'] = {'client_id': '',
                   'secret': '',
                   'callback': ''}

mc_list_ids = {'waitlist': '', 'attending': ''}

WAITLIST_LIMIT = 550
HACKATHON_TIME = datetime.strptime('2017-2-25', '%Y-%m-%d')
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'doc', 'docx', 'rtf']
