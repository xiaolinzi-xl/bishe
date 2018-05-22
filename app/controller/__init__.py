# from app.controller.activity import activity_bp
from .message import Message
from .chat import chat_bp
from .game import game_bp, GameError
from .recruit import recruit_bp
from .tactics import tactics_bp
from .team import team_bp
from .user import user_bp,Auth,UserError
from .activity import activity_bp
from .bag import bag_bp
from .index import MyIndexView
