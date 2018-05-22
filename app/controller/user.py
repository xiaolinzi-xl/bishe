import base64
import hashlib
import json
import time

from flask import Blueprint, request
from flask_restful import Api, Resource, reqparse

from app import db
from app.config import Config
from app.controller import Message
from app.controller.utils import MobSMS
from app.model import User
from ..config import sms_key

user_bp = Blueprint("user_bp", __name__)
user_api = Api(user_bp)
parser = reqparse.RequestParser()
query = db.session.query
add = db.session.add
commit = db.session.commit
rollback = db.session.rollback


class Auth:
    header = {'typ': 'JWT', 'alg': 'HS256'}
    payload = {
        'iss': 'iFantasy-android',
        'exp': None,
        'name': None
    }

    @staticmethod
    def generateTempToken(user):
        header = base64.urlsafe_b64encode(
            bytes(json.dumps(Auth.header), encoding='utf-8')
        )
        Auth.payload['exp'], Auth.payload['name'] = str(time.time()), str(user.tel)
        payload = base64.urlsafe_b64encode(
            bytes(json.dumps(Auth.payload), encoding='utf-8')
        )
        Auth.payload['exp'], Auth.payload['name'] = None, None
        sha256 = hashlib.sha256()
        sha256.update(header)
        sha256.update(payload)
        sha256.update(base64.urlsafe_b64encode(bytes(Config.SECRET_KEY, encoding="utf-8")))
        temptoken = header + b'.' + payload + b'.' + bytes(sha256.hexdigest(), encoding='utf-8')
        return str(temptoken, encoding='utf-8')

    @staticmethod
    def generateLoginToken(user):
        if not user:
            return Message(None, UserError.ILLEGAL_USER).response

        header = base64.urlsafe_b64encode(
            bytes(json.dumps(Auth.header), encoding='utf-8')
        )
        Auth.payload['exp'], Auth.payload['name'] = str(time.time()), str(user.id)
        payload = base64.urlsafe_b64encode(
            bytes(json.dumps(Auth.payload), encoding='utf-8')
        )
        Auth.payload['exp'], Auth.payload['name'] = None, None
        sha256 = hashlib.sha256()
        sha256.update(header)
        sha256.update(payload)
        sha256.update(base64.urlsafe_b64encode(bytes(Config.SECRET_KEY, encoding="utf-8")))
        logintoken = header + b'.' + payload + b'.' + bytes(sha256.hexdigest(), encoding='utf-8')
        return str(logintoken, encoding='utf-8')

    @staticmethod
    def generateAccessToken(user):
        if not user:
            raise Exception(UserError.ILLEGAL_USER)

        header = base64.urlsafe_b64encode(
            bytes(json.dumps(Auth.header), encoding='utf-8')
        )
        Auth.payload['exp'], Auth.payload['name'] = str(time.time()), str(user.id)
        payload = base64.urlsafe_b64encode(
            bytes(json.dumps(Auth.payload), encoding='utf-8')
        )
        Auth.payload['exp'], Auth.payload['name'] = None, None
        sha256 = hashlib.sha256()
        sha256.update(header)
        sha256.update(payload)
        sha256.update(base64.urlsafe_b64encode(bytes(Config.SECRET_KEY, encoding="utf-8")))
        accesstoken = header + b'.' + payload + b'.' + bytes(sha256.hexdigest(), encoding='utf-8')
        return str(accesstoken, encoding='utf-8')

    @staticmethod
    def authLoginToken(user, logintoken):
        return logintoken == user.logintoken

    @staticmethod
    def authAccessToken(user, accesstoken):
        return accesstoken == user.accesstoken

    @staticmethod
    def authToken(user_id, accesstoken):
        user = query(User).get(user_id)
        Auth.authAccessToken(user, accesstoken)


class UserError:
    ILLEGAL_USER = "Illegal user", -3
    AUTH_FAILED = "Authentication Failed", -3


class VerificationApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument('phone', type=str)
    parse.add_argument('code', type=str)
    parse.add_argument('zone', type=str)

    def post(self):
        args = self.parse.parse_args(strict=True)
        phone = args['phone']
        code = args['code']
        zone = args['zone']

        res = MobSMS(sms_key).verify_sms_code(zone, phone, code, debug=True)
        if res == 200:
            user = query(User).filter_by(tel=phone).first()
            if not user:
                user = User(None, phone, None, None, None, None);
                user.logintoken = Auth.generateTempToken(user)
                add(user)
                try:
                    commit()
                    msg = Message(user.user_full2dict(), None, 201)
                except Exception as e:
                    rollback()
                    print(e)
                    msg = Message(None, "cannot commit to db", -1)
                return msg.response
            return Message(user.user_full2dict(), None, 200).response
        elif res == 467:
            return Message(None, "请求校验验证码频繁", 467).response
        elif res == 468:
            return Message(None, "验证码错误", 468).response


class RegisterApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument('phone', type=str)
    parse.add_argument('nickname', type=str)

    def post(self):
        args = self.parse.parse_args(strict=True)
        phone = args['phone']
        nickname = args['nickname']
        temptoken = request.headers.get('Authorization')

        if temptoken:
            user = query(User).filter_by(tel=phone).first()
            if user and Auth.authLoginToken(user, temptoken):
                user.accesstoken = Auth.generateAccessToken(user)
                user.level = 1
                user.logintoken = Auth.generateLoginToken(user)
                user.money = 1000
                user.nickname = nickname
                try:
                    commit()
                    msg = Message(user.user_full2dict(), None, 200)
                except Exception as e:
                    rollback()
                    print(e)
                    msg = Message(None, "cannot commit to db", -1)
                return msg.response
        return Message(*UserError.AUTH_FAILED).response


class LoginApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument('phone', type=str)

    def post(self):
        args = self.parse.parse_args(strict=True)
        phone = args['phone']
        logintoken = request.headers.get('Authorization')

        if logintoken:
            user = query(User).filter_by(tel=phone).first()
            if user and Auth.authLoginToken(user, logintoken):
                user.accesstoken = Auth.generateAccessToken(user)
                try:
                    commit()
                    msg = Message(user.user_full2dict(), None, 200)
                except Exception as e:
                    rollback()
                    print(e)
                    msg = Message(None, "cannot commit to db", -1)
                return msg.response
        return Message(*UserError.AUTH_FAILED).response


class RefreshAccessTokenApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument('user_id', type=int)

    def post(self):
        args = self.parse.parse_args(strict=True)
        user_id = args['user_id']
        logintoken = request.headers.get('Authorization')

        if logintoken:
            user = query(User).get(user_id)
            if user:
                user.accesstoken = Auth.generateAccessToken(user)
                try:
                    commit()
                    msg = Message(user.accesstoken, None, 200)
                except Exception as e:
                    rollback()
                    print(e)
                    msg = Message(None, "cannot commit to db", -1)
                return msg.response
            return Message(*UserError.AUTH_FAILED).response


class LogoutApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument('user_id', type=int)

    def delete(self):
        args = self.parse.parse_args(strict=True)
        user_id = args['user_id']
        user = query(User).get(user_id)
        if not user:
            return Message(*UserError.ILLEGAL_USER).response
        user.accesstoken = None
        try:
            commit()
            msg = Message(user.user_full2dict(), None, 200)
        except Exception as e:
            rollback()
            print(e)
            msg = Message(None, "cannot commit to db", -1)
        return msg.response


class QueryUserApi(Resource):
    parse = reqparse.RequestParser()
    parse.add_argument('nickname', type=str)

    def get(self):
        args = self.parse.parse_args(strict=True)
        nickname = args['nickname']
        if nickname:
            user = query(User).filter_by(nickname=nickname).first()
            if user:
                return Message(user.user_part2dict(), None, 200).response
        return Message(*UserError.ILLEGAL_USER).response


user_api.add_resource(VerificationApi, '/verification')
user_api.add_resource(RegisterApi, '/register')
user_api.add_resource(LoginApi, '/login')
user_api.add_resource(RefreshAccessTokenApi, '/refresh')
user_api.add_resource(LogoutApi, '/logout')
user_api.add_resource(QueryUserApi, '/query')
