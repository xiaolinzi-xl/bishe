from app import db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(20))
    tel = db.Column(db.String(15))
    level = db.Column(db.Integer)
    money = db.Column(db.Integer)
    logintoken = db.Column(db.String(256))
    accesstoken = db.Column(db.String(256))

    def __init__(self, nickname, tel, level, money, logintoken, accesstoken):
        self.nickname, self.tel, self.level, self.money, self.logintoken, self.accesstoken = (
            nickname, tel, level, money, logintoken, accesstoken
        )

    def __repr__(self):
        return "<User %r>" % self.id

    def user_full2dict(self):
        return {
            'id': self.id,
            'nickname': self.nickname,
            'phone': self.tel,
            'level': self.level,
            'money': self.money,
            'logintoken': self.logintoken,
            'accesstoken': self.accesstoken
        }

    def user_part2dict(self):
        return {
            'id': self.id,
            'nickname': self.nickname
        }
