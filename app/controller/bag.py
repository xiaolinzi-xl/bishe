from flask import Blueprint
from flask_restful import Api, Resource,reqparse
from app import db
from app.model import BagPiece, BagEquip, BagProp, BagTrailCard
from app.model import Piece, Equip, PropUsing
from app.model import BagPlayer,PlayerBase
from app.model.bag import PlayerEquip
from app.controller import Message
from datetime import datetime,timedelta

bag_bp = Blueprint('bag_bp', __name__)
bag_api = Api(bag_bp)

query = db.session.query
add = db.session.add
delete = db.session.delete
commit = db.session.commit

class BagError:
    NO_PIECE = 'You have no pieces', -301
    NO_TRAIL_CARD = 'You have no trail cards', -302
    NO_EQUIP = 'You have no equip', -303
    NO_PROP = 'You have no Prop', -304
    NOT_ENOUGH_PIECE = 'You have no enough piece', -305
    NOT_ENOUGH_TRAIL_CARD = 'You have no this trail card', -306
    PLAYER_REPEAT = 'you already have this player', -307
    NO_PLAYER = 'You have no this player', -308


class BagMessage(Message):
    PIECE_LIST = 'Piece list', 301
    USING_PIECE_ADD_PLAYER = 'Using piece add a player', 302

    TRAIL_CARD_LIST = 'Trail card list', 303
    USING_TRAIL_CARD_ADD_PLAYER = 'Using trail card add a player', 304
    USING_TRAIL_CARD_ADD_DUETIME = 'Using trail card add duetime', 305

    EQUIP_LIST = 'Bag equip list', 306
    USING_EQUIP = 'Using equip', 307
    PLAYER_EQUIP_LIST = 'player equip list', 310
    UNEQUIP = 'unequip from player', 311

    PROP_LIST = 'Prop list', 308
    USING_PROP = 'Using prop', 309


    def __init__(self, result = None, error = '', state = 0):
        super(BagMessage, self).__init__(result, error, state)


#列出背包里的piece
class BagPieceApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type = int)

    def get(self):
        args = self.parser.parse_args()
        user_id = args['user_id']

        data = BagPiece.query.filter_by(user_id = user_id).all()
        if data is None or len(data) == 0:
            return BagMessage(None, *BagError.NO_PIECE).response

        result = []
        for each in data:
            each_data = {}
            each_data['name'] = each.player_base.name
            each_data['num'] = each.num
            each_data['total'] = query(Piece).filter_by(player_id = each.player_id).first().total_num
            each_data['pos1'] = each.player_base.pos1
            each_data['pos2'] = each.player_base.pos2

            result.append(each_data)

        return BagMessage(result, *BagMessage.PIECE_LIST).response


#使用piece合成player,
class UsingPieceApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type = int)
    parser.add_argument("player_id", type = int)

    def post(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        player_id = args['player_id']
        # 判断该user是否已经有这个player
        if BagPlayer.query.filter_by(user_id = user_id, player_id = player_id).first() is not None :
            return BagMessage(None, *BagError.PLAYER_REPEAT).response

        data = BagPiece.query.filter_by(user_id = user_id, player_id = player_id).first()
        #判断user是否有piece
        if data is None:
            return BagMessage(None, *BagError.NO_PIECE).response
        piece_data = {}
        piece_data['num'] = data.num
        piece_data['total_num'] = query(Piece).filter_by(player_id = player_id).first().total_num
        piece_data['name'] = data.player_base.name

        #判断piece 是否足够合成
        if piece_data['num'] < piece_data['total_num']:
            return BagMessage(None, *BagError.NOT_ENOUGH_PIECE).response

        # 消耗使用的piece
        if piece_data['num'] == piece_data['total_num']:
            db.session.delete(data)
            commit()
        else:
            new_num = piece_data['num'] - piece_data['total_num']
            data.num = new_num
            commit()
        # 合成player
        today = datetime.now()
        due = today.replace(year = today.year + 1)
        player = query(PlayerBase).filter_by(id = player_id).first()
        contract = '一年%d万，%d年%d月%d日签约，%d年%d月%d日到期' % (player.price, today.year, today.month, today.day, due.year, due.month, due.day)
        add(BagPlayer(user_id = user_id, player_id = player_id, score = player.score, salary = player.price, duedate = due, contract = contract))
        commit()
        return BagMessage(player.name, *BagMessage.USING_PIECE_ADD_PLAYER).response


#列出bag里的trail_card
class BagTrailCardApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type = int)

    def get(self):
        args = self.parser.parse_args()
        user_id = args['user_id']

        data = BagTrailCard.query.filter_by(user_id = user_id).all()
        if data is None or len(data) == 0:
            return BagMessage(None, *BagError.NO_TRAIL_CARD).response

        result = []
        for each in data:
            each_data = {}
            each_data['name'] = each.player.name
            each_data['num'] = each.num
            each_data['time'] = each.time
            each_data['pos1'] = each.player.pos1
            each_data['pos2'] = each.player.pos2
            result.append(each_data)
        return BagMessage(result, *BagMessage.TRAIL_CARD_LIST).response


#使用trail card 增加player/duetime
class UsingTrailCardApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type = int)
    parser.add_argument("player_id", type = int)

    def post(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        player_id = args['player_id']

        playerdata = query(BagPlayer).filter_by(user_id = user_id, player_id = player_id).first()
        trail_card = query(BagTrailCard).filter_by(user_id = user_id,player_id = player_id).first()
        if trail_card is None or trail_card.num <= 0:
            return BagMessage(None,*BagError.NOT_ENOUGH_TRAIL_CARD).response

        #若已有player,续duetime
        if playerdata is not None:
            due = playerdata.duedate
            playerdata.duedate = due + timedelta(trail_card.time)
            trail_card.num -= 1
            if trail_card.num <= 0:
                db.session.delete(trail_card)
            commit()
            return BagMessage(playerdata.player.name, *BagMessage.USING_TRAIL_CARD_ADD_DUETIME).response
        #若没有player,add a player
        else:
            today = datetime.today()
            due = today.replace(day = today.day + trail_card.time)
            player = query(PlayerBase).filter_by(id=player_id).first()
            #contract = '%d年%d月%d日，%d年%d月%d日到期' % (today.year, today.month, today.day, due.year, due.month, due.day)
            contract = 'start:%d:%d:%d,due:%d:%d:%d' % (today.year, today.month, today.day, due.year, due.month, due.day)
            add(BagPlayer(user_id = user_id, player_id = player_id, score = player.score, salary = player.price, duedate = due, contract = contract))
            trail_card.num -= 1
            if trail_card.num <= 0:
                db.session.delete(trail_card)
            commit()
            return BagMessage(player.name, *BagMessage.USING_TRAIL_CARD_ADD_PLAYER).response


#列出bag里的equip
class BagEquipApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type = int)
    parser.add_argument("type", type = int)

    def get(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        type = args['type']

        data = query(BagEquip).filter_by(user_id = user_id).all()

        if data is None or len(data) == 0:
            return BagMessage(None, *BagError.NO_EQUIP).response

        result = []
        for each in data:
            #若type == 0，查询所有否则只查询对应type
            if type == 0 or each.equip.type == type:
                each_data = {}
                each_data['name'] = each.equip.name
                each_data['num'] = each.num
                each_data['attr_ch_id'] = each.equip.attr_ch_id
                result.append(each_data)

        return BagMessage(result, *BagMessage.EQUIP_LIST).response


#使用bag里的equip
class UsingEquipApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type=int)
    parser.add_argument("equip_id", type=int)
    parser.add_argument("player_id", type=int)

    def post(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        equip_id = args['equip_id']
        player_id = args['player_id']


        bag_player_data = query(BagPlayer).filter_by(user_id = user_id,player_id = player_id).first()
        if bag_player_data is None:
            return BagMessage(None, *BagError.NO_PLAYER).response
        bag_player_id = bag_player_data.id

        if query(PlayerEquip).filter_by(bag_player_id = bag_player_id).first() is None:
            add(PlayerEquip(bag_player_id = bag_player_id,coat_id = None,pants_id = None,shoes_id = None))

        equip_data = query(Equip).filter_by(id = equip_id).first()
        type = equip_data.type
        old = query(PlayerEquip).filter_by(bag_player_id = bag_player_id).first()
        old_coat = old.coat_id
        old_pants = old.pants_id
        old_shoes = old.shoes_id
        #如果没穿着该装备，才脱下并穿上新装备。已穿着则直接不脱不穿
        if (equip_id != old_coat and equip_id != old_pants and equip_id != old_shoes):
            unequip_player(bag_player_id = bag_player_id,type = type)
            equip_player(equip_id = equip_id,bag_player_id = bag_player_id)

        result = {}
        pe_data = query(PlayerEquip).filter_by(bag_player_id = bag_player_id).first()

        if pe_data.coat_id is not None:
            result['coat_id'] = pe_data.coat_id
            result['coat_attr_id'] = query(Equip).filter_by(id = pe_data.coat_id).first().attr_ch_id
        else:
            result['coat_id'] = None
        if pe_data.pants_id is not None:
            result['pants_id'] = pe_data.pants_id
            result['pants_attr_id'] = query(Equip).filter_by(id = pe_data.pants_id).first().attr_ch_id
        else:
            result['pants_id'] = None
        if pe_data.shoes_id is not None:
            result['shoes_id'] = pe_data.shoes_id
            result['shoes_attr_id'] = query(Equip).filter_by(id = pe_data.shoes_id).first().attr_ch_id
        else:
            result['shoes_id'] = None

        commit()
        return BagMessage(result, *BagMessage.USING_EQUIP).response


class UnEquipApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("bag_player_id", type=int)
    parser.add_argument("type", type = int)

    def post(self):
        args = self.parser.parse_args()
        bag_player_id = args['bag_player_id']
        type = args['type']

        unequip_player(bag_player_id = bag_player_id, type = type)

        result = {}
        pe_data = query(PlayerEquip).filter_by(bag_player_id=bag_player_id).first()

        if pe_data.coat_id is not None:
            result['coat_id'] = pe_data.coat_id
            result['coat_attr_id'] = query(Equip).filter_by(id=pe_data.coat_id).first().attr_ch_id
        else:
            result['coat_id'] = None
        if pe_data.pants_id is not None:
            result['pants_id'] = pe_data.pants_id
            result['pants_attr_id'] = query(Equip).filter_by(id=pe_data.pants_id).first().attr_ch_id
        else:
            result['pants_id'] = None
        if pe_data.shoes_id is not None:
            result['shoes_id'] = pe_data.shoes_id
            result['shoes_attr_id'] = query(Equip).filter_by(id=pe_data.shoes_id).first().attr_ch_id
        else:
            result['shoes_id'] = None

        commit()
        return BagMessage(result, *BagMessage.UNEQUIP).response



def add_equip_in_bag(user_id, equip_id):
    if query(BagEquip).filter_by(user_id = user_id, equip_id = equip_id).first() is None:
        add(BagEquip(user_id = user_id, equip_id = equip_id, num = 1))
    else:
        num = query(BagEquip).filter_by(user_id = user_id, equip_id = equip_id).first().num
        num += 1;

    commit()

    return None

def minus_equip_in_bag(user_id, equip_id):
    equip = query(BagEquip).filter_by(user_id = user_id, equip_id = equip_id).first()
    equip.num -= 1
    if equip.num <= 0:
        delete(equip)

    commit()

    return None

def equip_player(bag_player_id, equip_id):

    data = query(BagPlayer).filter_by(id = bag_player_id).first()
    user_id = data.user_id
    minus_equip_in_bag(user_id = user_id, equip_id = equip_id)

    p_equip = query(PlayerEquip).filter_by(bag_player_id = bag_player_id).first()
    e_data = query(Equip).filter_by(id = equip_id).first()
    e_type = e_data.type
    if e_type == 1:
        p_equip.coat_id = equip_id
    elif e_type == 2:
        p_equip.pants_id = equip_id
    elif e_type == 3:
        p_equip.shoes_id = equip_id
    else:
        return ValueError

    commit()

    return None

def unequip_player(bag_player_id, type):
    # 取出待脱下的equip_id
    p_equip = query(PlayerEquip).filter_by(bag_player_id = bag_player_id).first()
    if p_equip is None:
        return
    if type == 1 and p_equip.coat_id is not None:
        equip_id = p_equip.coat_id
        p_equip.coat_id = None
    elif type == 2 and p_equip.pants_id is not None:
        equip_id = p_equip.pants_id
        p_equip.pants_id = None
    elif type == 3 and p_equip.shoes_id is not None:
        equip_id = p_equip.shoes_id
        p_equip.shoes_id = None
    else:
        return None

    # 脱下的装备返回背包
    user_id = query(BagPlayer).filter_by(id = bag_player_id).first().user_id
    add_equip_in_bag(user_id = user_id, equip_id = equip_id)
    commit()

    return None


#展示bag中拥有的球员穿着在身上的装备信息
class PlayerEquipApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("bag_player_id", type = int)

    def get(self):
        args = self.parser.parse_args()
        bag_player_id = args['bag_player_id']

        data = query(PlayerEquip).filter_by(bag_player_id = bag_player_id).first()
        if data is None:
            return BagMessage(None, *BagError.NO_EQUIP).response

        result = {}
        result['coat_id'] = data.coat_id
        result['pants_id'] = data.pants_id
        result['shoes_id'] = data.shoes_id

        return BagMessage(result, *BagMessage.PLAYER_EQUIP_LIST).response


#列出bag里的prop
class BagPropApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type = int)

    def get(self):
        args = self.parser.parse_args()
        user_id = args['user_id']

        data = query(BagProp).filter_by(user_id = user_id).first()
        #若没有，则记为各拥有０个fund_card,exp_card
        if data is None:
            add(BagProp(user_id = user_id,fund_card_num = 0, exp_card_num = 0))
            commit()
            data = query(BagProp).filter_by(user_id = user_id).first()
        result = {}
        result['fund_card_num'] = data.fund_card_num
        result['exp_card_num'] = data.exp_card_num
        return BagMessage(result, *BagMessage.PROP_LIST).response


#使用bag里的prop
class UsingPropApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument("user_id", type=int)
    parser.add_argument("prop_type", type=int)

    def post(self):
        args = self.parser.parse_args()
        user_id = args['user_id']
        prop_type = args['prop_type']

        #有效期限为3天
        time = 3
        data = query(BagProp).filter_by(user_id = user_id).first()
        if data is None:
            return BagMessage(None, *BagError.NO_PROP).response
        if (prop_type == 0 and data.fund_card_num <= 0) or (prop_type == 1 and data.exp_card_num <= 0):
            return BagMessage(None, *BagError.NO_PROP).response

        #消耗prop
        if prop_type == 0:
            data.fund_card_num -= 1
            commit()
        else:
            data.exp_card_num -= 1
            commit()

        #add duetime
        usingdata = query(PropUsing).filter_by(user_id = user_id,prop_type = prop_type).first()
        if usingdata is None:
            due = datetime.now() + timedelta(time)
            add(PropUsing(user_id = user_id, prop_type = prop_type, duetime = due))
            commit()
        else:
            usingdata.duetime = usingdata.duetime + timedelta(time)
            commit()

        res = query(PropUsing).filter_by(user_id = user_id,prop_type = prop_type).first()
        return BagMessage(res.duetime, *BagMessage.USING_PROP).response



# Setup the Api resource routing here

bag_api.add_resource(BagPieceApi,'/piecelist')
bag_api.add_resource(UsingPieceApi,'/usingpiece')

bag_api.add_resource(BagTrailCardApi,'/trailcardlist')
bag_api.add_resource(UsingTrailCardApi,'/usingtrailcard')

bag_api.add_resource(BagEquipApi,'/equiplist')
bag_api.add_resource(UsingEquipApi,'/usingequip')
bag_api.add_resource(UnEquipApi,'/unequip')
bag_api.add_resource(PlayerEquipApi,'/playerequiplist')

bag_api.add_resource(BagPropApi,'/proplist')
bag_api.add_resource(UsingPropApi,'/usingprop')
