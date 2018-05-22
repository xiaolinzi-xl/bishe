# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_restful import Api, Resource, reqparse
from app.model import BagPlayer, SeasonData, User, LineUp, PlayerBase
from app.controller import Message
from app.controller.bag import unequip_player
from app import db
from sqlalchemy import or_
import datetime

team_bp = Blueprint("team_bp", __name__)
team_api = Api(team_bp)


# 将数据转换成百分比
def switch_percent(data):
    str_num = str(float(data) * 100).split('.')
    if str_num[1][0] == '0':
        res = str_num[0] + '%'
    else:
        res = str_num[0] + '.' + str_num[1][0] + '%'
    return res


# 获取球员赛季数据
def get_season_data(data):
    result = []

    for season in data:
        season_data = {}
        season_data['season'] = season.season[2:]
        season_data['team_name'] = season.team_name
        season_data['gp'] = season.gp  # 出场
        season_data['min'] = season.min  # 时间
        season_data['pts'] = season.pts  # 得分

        season_data['reb'] = season.reb  # 篮板
        season_data['ast'] = season.ast  # 助攻
        season_data['stl'] = season.stl  # 抢断
        season_data['blk'] = season.blk  # 盖帽
        season_data['tov'] = season.tov  # 失误
        season_data['fg_pct'] = switch_percent(season.fg_pct)  # 投篮%
        season_data['fg3_pct'] = switch_percent(season.fg3_pct)  # 三分%
        season_data['ft_pct'] = switch_percent(season.ft_pct)  # 罚球%
        season_data['efg_pct'] = switch_percent(season.efg_pct)
        season_data['ts_pct'] = switch_percent(season.ts_pct)
        season_data['ortg'] = season.ortg
        season_data['drtg'] = season.drtg

        result.append(season_data)
    return result


# 获取球员基本信息
def get_player_base(player):
    result = {}

    result['name'] = player.name
    result['team_name'] = player.team.name
    result['cloth_num'] = player.cloth_num
    result['pos'] = player.pos1  # 默认取球员第一个位置
    result['score'] = player.score
    result['price'] = player.price
    # print(player.birthday)
    # print(type(player.birthday))
    birthday = str(player.birthday).split('-')
    # print(birthday)
    result['birthday'] = '{0}年{1}月{2}日'.format(*birthday)
    # result['birthday'] = player.birthday

    result['country'] = player.country
    result['height'] = player.height
    result['weight'] = player.weight
    result['armspan'] = player.armspan
    result['reach_height'] = player.reach_height
    result['draft'] = player.draft  # 选秀
    # result['image_url'] = get_image_url(player)

    return result


# 返回球员的图片地址
# def get_image_url(player):
#     image_url = player.id
#     return image_url



# 返回球员的位置
def get_pos(bag_player):
    pos = []
    pos.append(bag_player.player.pos1)
    if bag_player.player.pos2:
        pos.append(bag_player.player.pos2)
    return pos


# 返回球员的信息:名字 位置 背包ID
def get_player_info(bag_player_id, pos):
    bag_player = BagPlayer.query.filter_by(id=bag_player_id).first()
    res = {}
    if bag_player is None:
        return False, res
    res['bag_player_id'] = bag_player_id
    res['pos'] = pos
    res['name'] = bag_player.player.name

    return True, res


# 删除阵容某个具体的球员
def delete_player(lineup, bag_player_id):
    if lineup.c == bag_player_id:
        lineup.c = None
    elif lineup.pf == bag_player_id:
        lineup.pf = None
    elif lineup.sf == bag_player_id:
        lineup.sf = None
    elif lineup.pg == bag_player_id:
        lineup.pg = None
    else:
        lineup.sg = None


# 错误码 800-899
class TeamError:
    pass


# 返回给前端或安卓端的数据
class TeamMessage(Message):
    def __init__(self, result=None, error='', state=0):
        super(TeamMessage, self).__init__(result, error, state)


# 获取背包中所有球员信息,按照位置进行分类,默认是按照评分进行排序，也可以按照薪资排序
class PlayerListApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type=int, required=True)
    parser.add_argument("pos", type=str)  # 0-all,1-c,2-pf,3-sf,4-pg,5-sg
    parser.add_argument("order", type=str)  # 1-背包id,2-评分,3-薪资

    def get(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        # print(user_id)
        # order = args['order']
        # if order is None:
        #     order = '1'
        user = User.query.get(user_id)
        print(user)
        if user is None:
            return TeamMessage(error="非法用户",state=-801).response
        order = args.get('order','1')
        pos = args['pos']
        # print(pos)
        # print(order)
        db_pos_dict = {'0': 'all', '1': 'C', '2': 'F', '3': 'F', '4': 'G', '5': 'G'}
        real_pos = db_pos_dict.get(pos, 'all')  # 默认返回所有球员

        # print(type(pos))
        # print(pos)
        # print(order)
        now_time = datetime.datetime.now()
        if order == '1':
            data = BagPlayer.query.filter(BagPlayer.user_id == user_id, BagPlayer.duedate > now_time).all()
        elif order == '2':
            data = BagPlayer.query.filter(BagPlayer.user_id == user_id, BagPlayer.duedate > now_time).order_by(
                BagPlayer.score.desc()).all()
        else:
            # assert order == 'salary'
            data = BagPlayer.query.filter(BagPlayer.user_id == user_id, BagPlayer.duedate > now_time).order_by(
                BagPlayer.salary.desc()).all()
        result = []
        # if data is None or len(data) == 0:
        #     return TeamMessage(error="背包无球员", state=-802).response
        for player in data:
            if real_pos != 'all':
                # db_pos = pos[-1]
                # 过滤球员
                if player.player.pos1 != real_pos and player.player.pos2 != real_pos:
                    continue
                    # else:
                    #     tmp_pos = pos
            # else:
            #     tmp_pos = player.player.pos1
            player_data = {}
            player_data['bag_id'] = player.id
            player_data['id'] = player.player.id
            player_data['name'] = player.player.name
            player_data['pos1'] = player.player.pos1
            player_data['pos2'] = player.player.pos2
            player_data['score'] = player.score
            player_data['salary'] = player.salary
            # player_data['image_url'] = get_image_url(player.player)

            result.append(player_data)

        return TeamMessage(result).response


class BagPlayerApi(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument("user_id", type=int)
    parser.add_argument("bag_player_id", type=int)
    parser.add_argument('player_id', type=int)
    parser.add_argument("lineup_id", type=int)
    parser.add_argument("replace_player_id", type=int)
    parser.add_argument("pos", type=str)

    # 获取单个球员的基本信息
    def get(self):
        args = self.parser.parse_args()
        # print(args)
        player_id = args['player_id']
        if player_id:
            player = PlayerBase.query.filter_by(id=player_id).first()
            if not player:
                return TeamMessage(error='数据库无此球员', state=-801).response
            res = get_player_base(player)
            return TeamMessage(res).response

        bag_player_id = args['bag_player_id']
        data = BagPlayer.query.filter_by(id=bag_player_id).first()
        if data is None:
            return TeamMessage(error="背包内无此球员信息", state=-802).response

        result = get_player_base(data.player)
        result['score'] = data.score
        result['salary'] = data.salary
        result['contract'] = data.contract
        result.pop('price')

        return TeamMessage(result).response

    # 替换球员
    def put(self):
        args = self.parser.parse_args()
        lineup_id = args['lineup_id']
        bag_player_id = args['bag_player_id']
        replace_player_id = args['replace_player_id']
        pos = args['pos']
        if bag_player_id == replace_player_id:
            return TeamMessage(error="不能替换自己", state=-840).response

        bag_player = BagPlayer.query.filter_by(id=bag_player_id).first()
        replace_player = BagPlayer.query.filter_by(id=replace_player_id).first()

        if bag_player is None:
            return TeamMessage(error="无此球员信息", state=-850).response

        if replace_player is None:
            return TeamMessage(error="无此球员信息", state=-850).response

        db_pos = pos
        if len(db_pos) == 2:
            db_pos = pos[-1]
        if db_pos not in get_pos(bag_player):
            return TeamMessage(error="只能替换相同位置的球员", state=-860).response

        line_up = LineUp.query.filter_by(id=lineup_id).first()
        if line_up is None:
            return TeamMessage(error="你未创建该阵容", state=-861).response

        lineup_player_ids = [line_up.c, line_up.pf, line_up.sf, line_up.pg, line_up.sg]
        if bag_player_id in lineup_player_ids:
            return TeamMessage(error="阵容已有该球员", state=-862).response

        # 更换球员
        if pos == "C":
            line_up.c = bag_player_id
        elif pos == "PF":
            line_up.pf = bag_player_id
        elif pos == "SF":
            line_up.sf = bag_player_id
        elif pos == "SG":
            line_up.sg = bag_player_id
        elif pos == "PG":
            line_up.pg = bag_player_id

        db.session.commit()

        return TeamMessage(result="替换球员成功").response

    # 解约球员，获得资金补贴
    def delete(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        bag_player_id = args['bag_player_id']
        # print(user_id)
        # print(bag_player_id)

        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return TeamMessage(error="该用户还未注册", state=-805).response

        bag_player = BagPlayer.query.filter_by(id=bag_player_id).first()
        if bag_player is None:
            return TeamMessage(error="不能删除背包不存在的球员", state=-804).response
        money = bag_player.salary
        lineups = LineUp.query.filter(
            or_(LineUp.c == bag_player_id, LineUp.pf == bag_player_id, LineUp.sf == bag_player_id,
                LineUp.pg == bag_player_id, LineUp.sg == bag_player_id)).all()
        # print(lineups)
        if lineups is not None:
            for lineup in lineups:
                delete_player(lineup, bag_player_id)

        for i in range(1, 4):
            unequip_player(bag_player_id, i)

        db.session.delete(bag_player)
        user.money += money
        db.session.commit()

        return TeamMessage(result="删除成功,获取补贴{}万元".format(money)).response


# TODO：投篮热图不知怎么做

# 获取单个球员赛季的数据,默认展示常规赛的数据，可以切换成季后赛的数据
class SeasonDataApi(Resource):
    # type为1表示常规赛数据，为0表示季后赛数据
    parser = reqparse.RequestParser()
    parser.add_argument("bag_player_id", type=int)
    parser.add_argument("type", type=int)
    parser.add_argument("player_id", type=int)

    def get(self):
        args = self.parser.parse_args()
        bag_player_id = args['bag_player_id']
        player_base_id = args['player_id']
        print(bag_player_id)
        print(player_base_id)
        if player_base_id:
            player_id = player_base_id
        elif bag_player_id:
            bag_player = BagPlayer.query.filter_by(id=bag_player_id).first()
            if bag_player is None:
                return TeamMessage(error="背包无此球员", state=-832).response

            player_id = bag_player.player.id

        type = args['type']

        if type is None or type == '':
            type = 1

        if type == 1:
            data = SeasonData.query.filter_by(player_id=player_id).filter_by(is_regular=1).all()
        else:
            data = SeasonData.query.filter_by(player_id=player_id).filter_by(is_regular=0).all()

        if data is None or len(data) == 0:
            return TeamMessage(error="该球员无任何赛季数据", state=-803).response

        result = get_season_data(data)

        # 返回最近两年的数据
        return TeamMessage(result[:2]).response


# 创建阵容
class LineupApi(Resource):
    '''
     pos: c,pf,sf,pg,sg 的顺序
    '''

    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type=int)
    parser.add_argument("team_id", type=int)
    parser.add_argument("c", type=int)
    parser.add_argument("pf", type=int)
    parser.add_argument("sf", type=int)
    parser.add_argument("pg", type=int)
    parser.add_argument("sg", type=int)
    parser.add_argument("lineup_id", type=int)
    parser.add_argument('ostrategy_id', type=int)
    parser.add_argument('dstrategy_id', type=int)

    # 获取某个阵容信息
    def get(self):
        args = self.parser.parse_args()
        if 'lineup_id' not in args:
            return TeamMessage(error="不能没有阵容", state=-840).response
        lineup_id = args['lineup_id']

        lineup = LineUp.query.filter_by(id=lineup_id).first()
        if lineup is None:
            return TeamMessage(error="无此阵容信息", state=-841).response

        flag, res_c = get_player_info(lineup.c, 'C')
        flag, res_pf = get_player_info(lineup.pf, 'PF')
        flag, res_sf = get_player_info(lineup.sf, 'SF')
        flag, res_pg = get_player_info(lineup.pg, 'PG')
        flag, res_sg = get_player_info(lineup.sg, 'SG')

        res = [res_c, res_pf, res_sf, res_pg, res_sg]

        return TeamMessage(result=res).response

    # 创建阵容
    def post(self):
        args = self.parser.parse_args()

        user_id = args['user_id']
        team_id = args['team_id']
        player_id_c = args['c']
        player_id_pf = args['pf']
        player_id_sf = args['sf']
        player_id_pg = args['pg']
        player_id_sg = args['sg']

        ostrategy_id = args['ostrategy_id']
        dstrategy_id = args['dstrategy_id']

        player_c = BagPlayer.query.filter_by(id=player_id_c).first()
        player_pf = BagPlayer.query.filter_by(id=player_id_pf).first()
        player_sf = BagPlayer.query.filter_by(id=player_id_sf).first()
        player_pg = BagPlayer.query.filter_by(id=player_id_pg).first()
        player_sg = BagPlayer.query.filter_by(id=player_id_sg).first()

        if player_c is not None and 'C' not in get_pos(player_c):
            return TeamMessage(error="球员无法打C位置", state=-855).response
        if player_pf is not None and 'F' not in get_pos(player_pf):
            return TeamMessage(error="球员无法打PF位置", state=-856).response
        if player_sf is not None and 'F' not in get_pos(player_sf):
            return TeamMessage(error="球员无法打SF位置", state=-857).response
        if player_pg is not None and 'G' not in get_pos(player_pg):
            return TeamMessage(error="球员无法打PG位置", state=-858).response
        if player_sg is not None and 'G' not in get_pos(player_sg):
            return TeamMessage(error="球员无法打SG位置", state=-859).response

        lineup = LineUp(user_id=user_id, team_id=team_id, pf=player_id_pf, c=player_id_c, sf=player_id_sf,
                        sg=player_id_sg, pg=player_id_pg, ostrategy_id=ostrategy_id, dstrategy_id=dstrategy_id)
        db.session.add(lineup)

        db.session.commit()

        return TeamMessage(result="创建阵容成功").response

    # 修改阵容
    def put(self):
        args = self.parser.parse_args()
        lineup_id = args['lineup_id']

        lineup = LineUp.query.filter_by(id=lineup_id).first()
        if lineup is None:
            return TeamMessage(error="无此阵容信息", state=-841).response

        player_id_c = args['c']
        player_id_pf = args['pf']
        player_id_sf = args['sf']
        player_id_pg = args['pg']
        player_id_sg = args['sg']

        player_c = BagPlayer.query.filter_by(id=player_id_c).first()
        player_pf = BagPlayer.query.filter_by(id=player_id_pf).first()
        player_sf = BagPlayer.query.filter_by(id=player_id_sf).first()
        player_pg = BagPlayer.query.filter_by(id=player_id_pg).first()
        player_sg = BagPlayer.query.filter_by(id=player_id_sg).first()

        if player_c is not None:
            if 'C' in get_pos(player_c):
                lineup.c = player_id_c
            else:
                return TeamMessage(error="该球员无法打C位置", state=-855).response
        if player_pf is not None:
            if 'F' in get_pos(player_pf):
                lineup.pf = player_id_pf
            else:
                return TeamMessage(error="该球员无法打PF位置", state=-856).response
        if player_sf is not None:
            if 'F' in get_pos(player_sf):
                lineup.sf = player_id_sf
            else:
                return TeamMessage(error="该球员无法打SF位置", state=-857).response
        if player_pg is not None:
            if 'G' in get_pos(player_pg):
                lineup.pg = player_id_pg
            else:
                return TeamMessage(error="该球员无法打PG位置", state=-858).response
        if player_sg is not None:
            if 'G' in get_pos(player_sg):
                lineup.sg = player_id_sg
            else:
                return TeamMessage(error="该球员无法打SG位置", state=-859).response

        db.session.commit()

        return TeamMessage(result="修改阵容成功").response

    # 删除阵容
    def delete(self):
        args = self.parser.parse_args()
        lineup_id = args['lineup_id']

        lineup = LineUp.query.filter_by(id=lineup_id).first()
        if lineup is None:
            return TeamMessage(error="不能删除空阵容", state=-841).response
        db.session.delete(lineup)
        db.session.commit()
        return TeamMessage(result='删除阵容成功').response


# 获取用户阵容列表信息
class LineUpListApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type=int)

    def get(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        data = LineUp.query.filter_by(user_id=user_id).all()
        if data is None or len(data) == 0:
            return TeamMessage(error="您还未创建阵容", state=-806).response
        res = []
        for lineup in data:
            lineup_data = {}
            lineup_data['lineup_id'] = lineup.id
            lineup_data['name'] = lineup.team_info.name

            res.append(lineup_data)

        return TeamMessage(result=res).response


team_api.add_resource(PlayerListApi, '/player/lists')

team_api.add_resource(BagPlayerApi, '/players')

team_api.add_resource(SeasonDataApi, '/seasons')

team_api.add_resource(LineupApi, '/lineups')

team_api.add_resource(LineUpListApi, '/lineup/lists')
