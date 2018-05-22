from app import db

class Friend(db.Model):
    __tablename__ = "friend"
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'friend_id'),
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'))


    def __init__(self, user_id, friend_id):
        self.user_id, self.friend_id = (
            user_id, friend_id
        )

    def __repr__(self):
        return "<Friend %r, %r>" % (self.user_id, self.friend_id)
