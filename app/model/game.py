from app import db


class UserGame(db.Model):
    __tablename__ = 'user_game'
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    id = db.Column('id',db.Integer,primary_key = True)
    user_id = db.Column("user_id", db.ForeignKey('user.id'))
    time = db.Column('time', db.DateTime)

    pts = db.Column('pts',db.Integer)
    oreb = db.Column('oreb', db.FLOAT)
    dreb = db.Column('dreb',db.FLOAT)
    ast = db.Column(db.FLOAT)
    stl = db.Column(db.FLOAT)
    blk = db.Column(db.FLOAT)
    in_pts = db.Column(db.FLOAT)
    tov = db.Column(db.FLOAT)
    ft = db.Column(db.FLOAT)
    three_pt = db.Column(db.FLOAT)

    user = db.relationship('User', backref='usergame')
    
    def __init__(self, user_id, time, pts ,oreb, dreb, ast, stl, blk, in_pts, tov, ft, three_pt):
        self.user_id = user_id
        self.time = time
        (self.pts, self.oreb, self.dreb, self.ast, 
        self.stl, self.blk, self.in_pts, self.tov,
        self.ft, self.three_pt) = (
            pts, oreb, dreb, ast, stl, blk, in_pts, tov, ft, three_pt
        )

    def __repr__(self):
        return "<UserGame {0}, {1}>".format(self.user_id, self.time)

class UserMatch(db.Model):
    __tablename__ = 'user_match'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),primary_key=True)
    score = db.Column(db.FLOAT,default=1000)

    user = db.relationship('User', backref='usermatch')
    def __init__(self,user_id, score=1000):
        self.user_id = user_id
        self.score = score
    def __repr__(self):
        return "<UserMatch %r, %r>" % (self.user_id, self.score)

class InputData(db.Model):
    __tablename__ = "input_data"
    id = db.Column(db.Integer, primary_key=True)
    player_base_id = db.Column(db.Integer, db.ForeignKey('player_base.id'))
    pts = db.Column(db.Integer)
    fg_pct = db.Column(db.FLOAT)
    three_pt_pct = db.Column(db.FLOAT)
    fta = db.Column(db.FLOAT)
    oreb_pct = db.Column(db.FLOAT)
    dreb_pct = db.Column(db.FLOAT)
    ast_pct = db.Column(db.FLOAT)
    tov = db.Column(db.FLOAT)
    stl = db.Column(db.FLOAT)
    blk = db.Column(db.FLOAT)
    pf = db.Column(db.FLOAT)
    p_m = db.Column(db.FLOAT)

    def __init__(self, player_base_id,pts,fg_pct, three_pt_pct, fta, oreb_pct, dreb_pct, ast_pct, tov, stl, blk, pf, p_m):
        (self.player_base_id, self.pts, self.fg_pct, self.three_pt_pct, self.fta, 
         self.oreb_pct, self.dreb_pct, self.ast_pct, self.tov,self.stl, self.blk, self.pf, self.p_m) = (
            player_base_id, pts, fg_pct, three_pt_pct, fta, oreb_pct, dreb_pct, ast_pct, tov, stl, blk, pf, p_m)

    def __repr__(self):
        return "<InputData %r>" % self.id