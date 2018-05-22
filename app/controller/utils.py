import requests
import json
import base64
import hashlib
from ..model import User
from ..config import Config
from datetime import datetime,date
import time
from functools import singledispatch

class MobSMS:
    def __init__(self, appkey):
        self.appkey = appkey
        self.verify_url = 'https://webapi.sms.mob.com/sms/verify'

    def verify_sms_code(self, zone, phone, code, debug=False):
        if debug:
            return 200

        data = {'appkey': self.appkey, 'phone': phone, 'zone': zone, 'code': code}
        req = requests.post(self.verify_url, data=data, verify=False)
        if req.status_code == 200:
            j = req.json()
            return j.get('status', 500)
        return 500



@singledispatch
def toJson(value):
    return value

@toJson.register(datetime)
def _(value):
    return str(value)
@toJson.register(date)
def _(value):
    return str(value)

class Verify:
    
    @staticmethod
    def verifyUser(user_id):
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return False
        return user
