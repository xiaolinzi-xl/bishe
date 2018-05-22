from app import db


class PlayerBase(db.Model):
    __tablename__ = 'player_base'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    birthday = db.Column(db.Date)
    country = db.Column(db.String(45))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    armspan = db.Column(db.Float)
    reach_height = db.Column(db.Float)
    draft = db.Column(db.String(255))

    # season_data_id = db.Column(db.Integer, db.ForeignKey('season_data.id'))
    team_id = db.Column(db.Integer, db.ForeignKey("team_info.id"))
    cloth_num = db.Column(db.Integer)
    pos1 = db.Column(db.String(2))
    pos2 = db.Column(db.String(2))
    price = db.Column(db.Integer)
    score = db.Column(db.Integer)

    team = db.relationship("TeamInfo", backref='playerbase')

    def __init__(self, name, birthday, country, height, wieght, armspan,
                 reach_height, draft, team_id, cloth_num, pos1, pos2, price, score):
        (self.name, self.birthday, self.country, self.height, self.wieght, self.armspan,
         self.reach_height, self.draft, self.team_id,
         self.cloth_num, self.pos1, self.pos2, self.price, self.score) = (name, birthday, country,
                                                                          height, wieght, armspan, reach_height, draft,
                                                                          team_id, cloth_num, pos1, pos2, price, score)

    def __repr__(self):
        return "<PlayerBase %r : %r>" % (self.id, self.name)


class TeamInfo(db.Model):
    __tablename__ = 'team_info'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    city = db.Column(db.String(45))
    intro = db.Column(db.String(255))

    def __init__(self, name, city, intro):
        self.name, self.city, self.intro = (
            name, city, intro)

    def __repr__(self):
        return "<TeamInfo %r>" % self.id


class SeasonData(db.Model):
    __tablename__ = 'season_data'
    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.String(15)) # 赛季时间
    is_regular = db.Column(db.Boolean)
    player_id = db.Column(db.Integer, db.ForeignKey('player_base.id'))
    player = db.relationship('PlayerBase', backref='seasondata')

    team_name = db.Column(db.String(255))
    gp = db.Column(db.Integer)
    min = db.Column(db.Float)
    reb = db.Column(db.Float)
    fg_pct = db.Column(db.Float)
    fg3_pct = db.Column(db.Float)
    ft_pct = db.Column(db.Float)

    pts = db.Column(db.Float)
    ast = db.Column(db.Float)
    oreb = db.Column(db.Float)
    dreb = db.Column(db.Float)
    stl = db.Column(db.Float)
    blk = db.Column(db.Float)
    tov = db.Column(db.Float)
    fgm = db.Column(db.Float)
    fga = db.Column(db.Float)
    fg3m = db.Column(db.Float)

    efg_pct = db.Column(db.Float)
    ts_pct = db.Column(db.Float)
    ortg = db.Column(db.Float)
    drtg = db.Column(db.Float)


    def __init__(self, season, is_regular):
        self.season, self.is_regular = (season, is_regular)

    def __repr__(self):
        return "<SeasonData %r>" % self.id


class BagPlayer(db.Model):
    __tablename__ = "bag_player"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('player_base.id'))
    score = db.Column(db.Integer)
    salary = db.Column(db.Integer)
    #input_data_id = db.Column(db.Integer, db.ForeignKey('input_data.id'))
    duedate = db.Column(db.DateTime)
    contract = db.Column(db.String(255))

    user = db.relationship('User', backref='bagplayer')
    player = db.relationship('PlayerBase', backref='bagplayer')
    #input_data = db.relationship('InputData', backref='bagplayer')

    def __init__(self, user_id, player_id, score, salary, duedate,contract):

        self.user_id, self.player_id, self.score, self.salary,  self.duedate,self.contract = (
            user_id, player_id, score, salary, duedate, contract
        )

    def __repr__(self):
        return "<BagPlayer %r>" % self.id


class LineUp(db.Model):
    __tablename__ = "lineup"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team_info.id'))
    pf = db.Column(db.Integer, db.ForeignKey('bag_player.id'))
    c = db.Column(db.Integer, db.ForeignKey('bag_player.id'))
    sf = db.Column(db.Integer, db.ForeignKey('bag_player.id'))
    sg = db.Column(db.Integer, db.ForeignKey('bag_player.id'))
    pg = db.Column(db.Integer, db.ForeignKey('bag_player.id'))
    ostrategy_id = db.Column(db.Integer, db.ForeignKey('ostrategy.id'))
    dstrategy_id = db.Column(db.Integer, db.ForeignKey('dstrategy.id'))

    user = db.relationship('User', backref='lineup' )
    team_info = db.relationship('TeamInfo', backref='lineup' )

    ostrategy = db.relationship('OStrategy', backref='lineup')
    dstrategy = db.relationship('DStrategy', backref='lineup')
    def __init__(self, user_id, team_id, pf, c, sf, sg, pg, ostrategy_id, dstrategy_id):
        self.user_id, self.team_id, self.pf, self.c, self.sf, self.sg, self.pg, self.ostrategy_id, self.dstrategy_id = (
            user_id, team_id, pf, c, sf, sg, pg, ostrategy_id, dstrategy_id
        )

    def __repr__(self):
        return "<LineUp %r>" % self.id
