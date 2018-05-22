from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from .config import config, Config
from flask_appbuilder import AppBuilder
import jpush
db = SQLAlchemy()
_jpush = jpush.JPush(Config.app_key, Config.master_secret)
_jpush.set_logging('DEBUG')
from app.controller import MyIndexView
appbuilder = AppBuilder(indexview=MyIndexView)
api_version = 'v1'



def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    db.app = app
    db.init_app(app)
    appbuilder.app = app
    appbuilder.init_app(app,db.session)

    
    from app.controller import Auth,UserError,Message
    from app.model import User
    #@app.before_request
    #def before_request():
    #    user_id = request.form.get('user_id')
    #    token = request.headers.get('Authorization')
    #    if not Auth.authToken(user_id, token):
    #        return str(Message(None, *UserError.AUTH_FAILED))

    from .controller import user_bp, bag_bp, game_bp, \
        tactics_bp, team_bp, activity_bp, chat_bp, recruit_bp
    app.register_blueprint(user_bp, url_prefix='/api/v1/user')
    app.register_blueprint(game_bp, url_prefix="/api/v1/game")
    app.register_blueprint(bag_bp, url_prefix="/api/v1/bag")
    app.register_blueprint(tactics_bp, url_prefix="/api/v1/tactics")
    app.register_blueprint(team_bp, url_prefix="/api/v1/team")
    app.register_blueprint(activity_bp, url_prefix="/api/v1/activity")
    app.register_blueprint(chat_bp, url_prefix="/api/v1/chat")
    app.register_blueprint(recruit_bp, url_prefix="/api/v1/recruit")

    from app.controller.ibg import AttrChModelView, EquipModelView, OStrategyModelView, DStrategyModelView, ThemeModelView, FundTypeModelView
    appbuilder.add_view(AttrChModelView,'属性')
    appbuilder.add_view(EquipModelView,'装备')
    appbuilder.add_view(OStrategyModelView,' 进攻策略')
    appbuilder.add_view(DStrategyModelView,' 防守策略')
    appbuilder.add_view(ThemeModelView, '主题')
    appbuilder.add_view(FundTypeModelView, '基金')

    """
        Application wide 404 error handler
    """
    @appbuilder.app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', base_template=appbuilder.base_template, appbuilder=appbuilder), 404

    #db.create_all()
    # from app.controller.recruit import Recom,Recommend
    # if not Recom.recom:
    #     print('start init recommendation system, waiting ...')
    #     Recom.recom = Recommend()
    #     print('init successfully')
    

    return app
