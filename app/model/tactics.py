from app import db

class OStrategy(db.Model):
    __tablename__ = "ostrategy"

    id = db.Column(db.Integer, primary_key=True)
    intro = db.Column(db.Text(512))
    sg_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
    pg_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
    sf_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
    pf_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
    c_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
   
    sg = db.relationship('AttrCh',foreign_keys=sg_id)
    sf = db.relationship('AttrCh',foreign_keys=sf_id)
    pg = db.relationship('AttrCh',foreign_keys=pg_id)
    pf = db.relationship('AttrCh',foreign_keys=pf_id)
    c = db.relationship('AttrCh',foreign_keys=c_id)

    def __repr__(self):
        return '<oOStrategy %r>' % self.id
class DStrategy(db.Model):
    __tablename__ = "dstrategy"

    id = db.Column(db.Integer, primary_key=True)
    intro = db.Column(db.Text(512))
    sg_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
    pg_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
    sf_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
    pf_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
    c_id = db.Column(db.Integer, db.ForeignKey('attr_ch.id'))
   
    sg = db.relationship('AttrCh',foreign_keys=sg_id)
    sf = db.relationship('AttrCh',foreign_keys=sf_id)
    pg = db.relationship('AttrCh',foreign_keys=pg_id)
    pf = db.relationship('AttrCh',foreign_keys=pf_id)
    c = db.relationship('AttrCh',foreign_keys=c_id)


    def __repr__(self):
        return "<DStrategy %r>" % self.id


class AttrCh(db.Model):
    __tablename__ = 'attr_ch'
    id = db.Column(db.Integer, primary_key=True)

    comment = db.Column(db.String(50))
    order = db.Column(db.String(200),default='fg_pct - three_pt_pct - fta_pct - oreb_pct - dreb_pct - ast_pct - tov_pct - stl_pct - blk_pct - pf_pct')
    fg_pct = db.Column(db.FLOAT,default=0)
    three_pt_pct = db.Column(db.FLOAT,default=0)
    fta_pct = db.Column(db.FLOAT,default=0)
    oreb_pct = db.Column(db.FLOAT,default=0)
    dreb_pct = db.Column(db.FLOAT,default=0)
    ast_pct = db.Column(db.FLOAT,default=0)
    tov_pct = db.Column(db.FLOAT,default=0)
    stl_pct = db.Column(db.FLOAT,default=0)
    blk_pct = db.Column(db.FLOAT,default=0)
    pf_pct = db.Column(db.FLOAT,default=0)

    def __repr__(self):
        return '<AttrCh %r : %r>' % (self.id, self.comment)
