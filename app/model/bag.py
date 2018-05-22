from app import db



class BagEquip(db.Model):
    __tablename__ = "bag_equip"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    equip_id = db.Column(db.Integer, db.ForeignKey('equip.id'))
    num = db.Column(db.Integer)

    user = db.relationship("User", backref='bagequip')
    equip = db.relationship("Equip")

    def __init__(self,  user_id, equip_id, num):
        self.user_id, self.equip_id, self.num = (user_id, equip_id, num)

    def __repr__(self):
        return "<BagEquip %r>" % (self.id)


class Equip(db.Model):
    __tablename__ = 'equip'
    id = db.Column(db.Integer, primary_key=True)
    #type = 1,2,3：coat,pants,shoes
    type = db.Column(db.Integer)
    name = db.Column(db.String(45))
    attr_ch_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))

    attr_ch = db.relationship('AttrCh')

    def __init__(self, type, name, attr_ch_id):
        self.type, self.name, self.attr_ch_id = (type, name, attr_ch_id)

    def __repr__(self):
        return "<Equip %r, %r, %r, %r>" % (self.id, self.type, self.name, self.attr_ch_id)


class PlayerEquip(db.Model):
    __tablename__ = "player_equip"
    __table_args__ = (
        db.PrimaryKeyConstraint('bag_player_id'),
    )
    bag_player_id = db.Column(db.Integer, db.ForeignKey("bag_player.id"))
    coat_id = db.Column(db.Integer)
    pants_id = db.Column(db.Integer)
    shoes_id = db.Column(db.Integer)

    bag_player = db.relationship("BagPlayer", backref='playerequip')

    def __init__(self,bag_player_id,coat_id,pants_id,shoes_id):
        self.bag_player_id,self.coat_id,self.pants_id,self.shoes_id = (
            bag_player_id, coat_id, pants_id, shoes_id
        )

    def __repr__(self):
        return "<PlayerEquip %r %r %r %r>" % (self.bag_player_id, self.coat_id, self.pants_id, self.shoes_id)




class BagPiece(db.Model):
    __tablename__ = "bag_piece"
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'player_id'),
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    player_id = db.Column(db.Integer, db.ForeignKey("player_base.id"))
    num = db.Column(db.Integer)

    user = db.relationship('User', backref='bagpiece')
    player_base = db.relationship('PlayerBase', backref='bagpiece')

    def __init__(self, user_id, player_id, num):
        self.user_id, self.player_id, self.num = (
            user_id, player_id, num
        )

    def __repr__(self):
        return "<BagPiece %r, %r>" % (self.user_id, self.player_id)


class Piece(db.Model):
    __tablename__ = 'piece'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player_base.id'))
    total_num = db.Column(db.Integer)

    player = db.relationship('PlayerBase', backref='piece')

    def __init__(self, player_id, total_num):
        self.player_id, self.total_num = (player_id, total_num)

    def __repr__(self):
        return "<Piece %r, %r, %r>" % (self.id, self.player_id, self.total_num)


class BagProp(db.Model):
    __tablename__ = "bag_prop"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True, autoincrement=False)
    fund_card_num = db.Column(db.Integer)
    exp_card_num = db.Column(db.Integer)

    user = db.relationship('User', backref='bagprop')

    def __init__(self, user_id, fund_card_num, exp_card_num):
        self.user_id, self.fund_card_num, self.exp_card_num = (
            user_id, fund_card_num, exp_card_num
        )

    def __repr__(self):
        return "<BagProp %r, %r, %r>" % (self.user_id, self.fund_card_num, self.exp_card_num)


class BagTrailCard(db.Model):
    __tablename__ = "bag_trail_card"
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'player_id','time'),
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('player_base.id'))
    num = db.Column(db.Integer)
    time = db.Column(db.Integer)

    user = db.relationship('User', backref='bagtrailcard')
    player = db.relationship('PlayerBase', backref='bagtrailcard')

    def __init__(self, user_id, palyer_id, num, time):
        self.user_id, self.player_id, self.num, self.time = (
            user_id, palyer_id, num, time
        )

    def __repr__(self):
        return "<BagTrailCard %r, %r, %r, %r>" % (self.user_id, self.player_id, self.num, self.time)


class PropUsing(db.Model):
    __tablename__ = "prop_using"
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'prop_type'),
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # prop_id == 0:fund_card
    # prop_id == 1:exp_card
    prop_type = db.Column(db.Integer)
    duetime = db.Column(db.DateTime)

    user = db.relationship('User', backref='propusing')

    def __init__(self, user_id, prop_type, duetime):
        self.user_id, self.prop_type, self.duetime = (
            user_id, prop_type, duetime
        )

    def __repr__(self):
        return "<PropUsing %r, %r, %r>" % (self.user_id, self.prop_type, self.duetime)
