from .activity import Theme, Vip, VipCard, Fund, FundType
from .bag import BagEquip, BagPiece, BagProp, PropUsing,Equip,Piece,BagTrailCard
from .chat import Friend
from .game import UserGame, UserMatch, InputData
from .tactics import OStrategy, AttrCh,DStrategy
from .team import PlayerBase,TeamInfo, SeasonData, BagPlayer, LineUp
from .user import User
from .recruit import Recruit,Sim,PlayerStat,Like

if __name__ == "__main__":
    user1 = User('user1','120',1,1200)
    user2 = User('user2','110',1,1200)
    user1.token = 'debug'
    user2.token = 'debug'
    db.session.add_all([user1,user2])
    db.session.commit()

    team = TeamInfo('Team','xian','niubi')
    db.session.add(team)
    db.session.commit()
    import datetime
    players = []
    for i in range(5):
        player = PlayerBase('player '+str(i),datetime.datetime.date(),
        'China',1.80,100,2.3,2.5,"draft ",team.id,12,'c',None,
        1000,500
        )
        players.append(player)
    db.session.add_all(players)
    db.session.commit()
    inputdata = InputData()
    att = AttrCh()
    db.session.add_all([inputdata,att])
    db.session.commit()
    s = [att.id]*10
    s = Strategy(*s)
    db.session.add(s)
    db.session.commit(s)
    lineups = []
    for user in [user1, user2]:
        db.session.add(UserMatch(user.id))
        db.session.commit()
        bagPlayers = []
        for player in players:
            bagPlayers.append(BagPlayer(user.id, player.id, player.score,player.price,
            inputdata.id, datetime.datetime.now()+datetime.timedelta(days=1),
            'contract'
            ))
        db.session.add_all(bagPlayers)
        db.sesson.commit()
            
        lineups.append(LineUp(user.id, team.id, bagPlayers[0].id,
        bagPlayers[1].id, bagPlayers[2].id,bagPlayers[3].id,
        bagPlayers[4].id,s.id))
    db.session.add_all(lineups)
    db.sessio.commit()
