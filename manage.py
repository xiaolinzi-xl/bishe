from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell

from app import create_app, db, appbuilder
from app.model import * #SeasonTheme, Vip, VipCard, Fund, FundType,BagEquip, BagPiece, BagPlayer, BagProp, PropUsing, InputData,Equip,Piece,BagTrailCard,Friend, GameHistory, UserGame,Strategy, AttrCh,PlayerBase,TeamInfo,User, LineUp

def make_shell_context():
    return dict(app=app, db=db,
    SeasonData=SeasonData,Theme=Theme, Vip = Vip, 
    VipCard = VipCard, Fund=Fund, FundType=FundType, 
    BagEquip=BagEquip, BagPlayer=BagPlayer, BagPiece=BagPiece,
    BagProp=BagProp,PropUsing=PropUsing,InputData=InputData,
    Recruit=Recruit,Equip=Equip,Piece=Piece,BagTrailCard=BagTrailCard,Friend=Friend,
    UserGame=UserGame, DStrategy=DStrategy,OStrategy=OStrategy,AttrCh=AttrCh, UserMatch=UserMatch,
    PlayerBase=PlayerBase,TeamInfo=TeamInfo,User=User, LineUp=LineUp,
    Sim=Sim,PlayerStat=PlayerStat,Like = Like
    )

app= create_app("develop")

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

manager.add_command("shell", Shell(make_context=make_shell_context))

if __name__ == "__main__":
    manager.run()
