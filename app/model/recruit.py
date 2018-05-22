from app import db


class Recruit(db.Model):
    __tablename__ = "recruit"

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    num = db.Column(db.Integer, default=0)
    time = db.Column(db.DateTime)
    
    user = db.relationship('User',backref='recruit')

    def __init__(self,user_id,num,time):
        self.user_id = user_id
        self.num = num
        self.time = time

    def __repr__(self):
        return "<Recruit %r>" % self.user_id

class Sim(db.Model):
    __tablename__ = "recom_sim"

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    player_one = db.Column(db.Integer, db.ForeignKey('player_base.id'), nullable=False)
    player_two = db.Column(db.Integer, db.ForeignKey('player_base.id'), nullable=False)
    sim = db.Column(db.FLOAT)

    def __init__(self,player_one,player_two,sim):
        self.player_one=player_one
        self.player_two=player_two
        self.sim=sim

    def __repr__(self):
        return "<Sim %r, %r>" % (self.player_one,self.player_two)

class PlayerStat(db.Model):##预先建立好,static
    __tablename__ = "recom_player"

    player_id = db.Column(db.Integer, db.ForeignKey('player_base.id'), primary_key=True,nullable=False)
    mode = db.Column(db.Integer)
    popular= db.Column(db.Integer)

    def __init__(self,player_id,mode,popular):
        self.player_id=player_id
        self.mode = mode
        self.popular=popular

    def __repr__(self):
        return "<PlayerStat %r>" % self.player_id

class Like(db.Model):##static
    __tablename__ = "recom_like"

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    player_one = db.Column(db.Integer, db.ForeignKey('player_base.id'), nullable=False)
    player_two = db.Column(db.Integer, db.ForeignKey('player_base.id'), nullable=False)
    like = db.Column(db.FLOAT)

    def __init__(self,player_one,player_two,like):
        self.player_one=player_one
        self.player_two=player_two
        self.like=like

    def __repr__(self):
        return "<Like %r, %r>" % (self.player_one,self.player_two)