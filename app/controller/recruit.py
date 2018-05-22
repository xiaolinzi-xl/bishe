from flask import Blueprint
from flask_restful import Api, Resource, reqparse
from app import db
from app.model import Recruit, User, PlayerBase, BagPlayer, BagTrailCard, BagPiece, BagProp, Theme, PlayerStat
from .message import Message
from .recommend import Recommend
from random import choice, random, sample
import datetime

recruit_bp = Blueprint('recruit_bp', __name__)
recruit_api = Api(recruit_bp)
parser = reqparse.RequestParser()
query = db.session.query
add = db.session.add
commit = db.session.commit
rollback = db.session.rollback
parser.add_argument('user_id', type=int)
parser.add_argument('player_id', type=int)
parser.add_argument('order', type=int)  # 1-score,2-price
parser.add_argument('pos', type=int)  # 0-all,1-c,2-pf,3-sf,4-pg,5-sg
parser.add_argument('theme_id', type=int)
parser.add_argument('bag_player_id', type=int)


class State:
    ArgError = "arg is incorrect", -250
    NoMoney = "no enough money", -251
    OwnPlayer = "have owned the player", -252  # get piece if the player
    FailCommit = "cannot commit to db", -201


class rMessage(Message):
    def __init__(self, result=None, error=('', 0)):
        if error[1] < 0:
            super(rMessage, self).__init__(result, error[0], error[1])
        else:
            super(rMessage, self).__init__(result)


class GetRecruit(Resource):
    '''
    fetch recruit num and time to recruit freely
    return {num:num of recruit to get one player,
            time:xx:xx:xx or null if ready to recrresult=uit freely}
    '''

    def get(self):
        args = parser.parse_args()
        user = query(User).get(args['user_id'])
        if user is None:
            return rMessage(error=State.ArgError).response
        info = query(Recruit).get(args['user_id'])
        if info is None:
            info = Recruit(user.id, 0, datetime.datetime.now())
            add(info)
            try:
                commit()
            except Exception as e:
                rollback()
                print(e)
                return rMessage(error=State.FailCommit).response
        delta = (datetime.datetime.now() - info.time)
        delta = datetime.timedelta(days=delta.days, seconds=delta.seconds)
        res = {'num': 3 - info.num}
        if delta.days > 0 or delta.seconds > 18000:
            res['time'] = None
        else:
            res['time'] = (datetime.timedelta(seconds=18000) - delta).seconds
        return rMessage(res).response


def __toList__(data):
    res = list()
    for item in data:
        res.append(item[0])
    return res


def __toSet__(data):
    res = set()
    for item in data:
        res.add(item[0])
    return res


def __randomPick__(lists, prob):
    r = random()
    cum = 0.0
    for item, item_prob in zip(lists, prob):
        cum += item_prob
        if r < cum: break
    return item


def __commit__(mes=None):
    try:
        commit()
        return mes
    except Exception as e:
        rollback()
        print(e)
        return rMessage(error=State.FailCommit)


def selectPlayer(type, pos=None):
    score = PlayerBase.score
    id = PlayerBase.id
    pos1 = PlayerBase.pos1
    pos2 = PlayerBase.pos2
    if type == 0:
        res = query(id).filter(score >= 90)
    if type == 1:
        res = query(id).filter(score < 90, score >= 80)
    if type == 2:
        res = query(id).filter(score < 80, score >= 70)
    if type == 3:
        res = query(id).filter(score < 70)
    if pos:
        res = res.filter((pos1 == pos) | (pos2 == pos))
    return __toSet__(res.all())


def addPlayer(user_id, player):
    today = datetime.datetime.today()
    duedate = today.replace(year=today.year + 1)
    contract = '一年%d万，%d年%d月%d日签约，%d年%d月%d日到期' % (player.price, today.year,
                                                  today.month, today.day, duedate.year, duedate.month, duedate.day)
    add(BagPlayer(user_id, player.id, player.score, player.price, duedate, contract))
    return {"name": player.name, "id": player.id, "type": "player"}


def getPlayer(user_id, level):
    if level == 1:
        player_class = [0, 1, 2]
        prob = [0.01, 0.09, 0.9]
    else:
        player_class = [0, 1]
        prob = [0.02, 0.98]
    players = selectPlayer(__randomPick__(player_class, prob))
    player_id = choice(list(players))
    ownplayer = getValidPlayer(user_id)
    if player_id not in ownplayer:
        player = query(PlayerBase).get(player_id)
        return addPlayer(user_id, player)
    else:
        return player_id


def genTrial(user_id):
    ownplayer = getValidPlayer(user_id)
    player_class = [0, 1, 2, 3]
    prob = [0.3, 0.4, 0.2, 0.1]
    players = selectPlayer(__randomPick__(player_class, prob))
    new_players = players - ownplayer
    if new_players:
        players = new_players
    player_id = choice(list(players))
    time_class = [1, 3, 5]
    prob = [0.85, 0.1, 0.05]
    time = __randomPick__(time_class, prob)
    return {"id": player_id, "time": time}


def genPiece():
    player_class = [0, 1, 2]
    prob = [0.05, 0.4, 0.55]
    players = selectPlayer(__randomPick__(player_class, prob))
    player_id = choice(list(players))
    num_class = [1, 5, 10, 15]
    prob = [0.45, 0.4, 0.1, 0.05]
    num = __randomPick__(num_class, prob)
    return {"id": player_id, "num": num}


def getProp(user_id):
    prop_type = ['trail', 'piece', 'fund', 'exp']
    prob = [0.2, 0.6, 0.1, 0.1]
    ptype = __randomPick__(prop_type, prob)
    if ptype == 'trail':
        if Recom.recom:
            res = Recom.recom.genTrial(user_id)
            print('recom trial')
        else:
            res = genTrial(user_id)
        if not res:
            res = genTrial(user_id)
        player = query(PlayerBase).get(res['id'])
        trail_card = query(BagTrailCard).get((user_id, player.id, res['time']))
        if trail_card:
            trail_card.num += 1
        else:
            add(BagTrailCard(user_id, player.id, 1, res['time']))
        return {'name': player.name, 'time': res['time'], "id": player.id, "type": "trail"}
    if ptype == 'piece':
        if Recom.recom:
            res = Recom.recom.genPiece()
            print('recom piece')
        else:
            res = genPiece()
        player = query(PlayerBase).get(res['id'])
        piece = query(BagPiece).get((user_id, player.id))
        if piece:
            piece.num += res['num']
        else:
            add(BagPiece(user_id, player.id, res['num']))
        return {'name': player.name, 'num': res['num'], "id": player.id, "type": "piece"}
    prop = query(BagProp).get(user_id)
    if ptype == 'fund':
        if prop:
            prop.fund_card_num += 1
        else:
            add(BagProp(user_id, 1, 0))
        return {"type": "fund"}
    if ptype == 'exp':
        if prop:
            prop.exp_card_num += 1
        else:
            add(BagProp(user_id, 0, 1))
        return {"type": "exp"}


def toPiece(user_id, player_id):
    player = query(PlayerBase).get(player_id)
    num = player.piece[0].total_num
    piece = query(BagPiece).get((user_id, player.id))
    if piece:
        piece.num += num
    else:
        add(BagPiece(user_id, player.id, num))
    return {'name': player.name, 'num': num, "id": player.id, "type": "piece"}


def getValidPlayer(user_id):
    players = set()
    now = datetime.datetime.now()
    bagplayer = query(BagPlayer).filter(BagPlayer.user_id == user_id).all()
    for item in bagplayer:
        if item.duedate > now:
            players.add(item.player_id)
    return players


class OneRecruit(Resource):
    def post(self):
        args = parser.parse_args()
        r_info = query(Recruit).get(args['user_id'])
        if r_info is None:
            return rMessage(error=State.ArgError).response
        u_info = r_info.user
        delta = (datetime.datetime.now() - r_info.time)
        delta = datetime.timedelta(days=delta.days, seconds=delta.seconds)
        if delta.days > 0 or delta.seconds > 18000:
            r_info.time = datetime.datetime.now()
        else:
            if u_info.money >= 100:
                u_info.money -= 100
            else:
                return rMessage(error=State.NoMoney).response
        if r_info.num == 2:
            res = getPlayer(u_info.id, 1)
            if isinstance(res, int):
                res = toPiece(u_info.id, res)
        else:
            res = getProp(u_info.id)
        r_info.num = (r_info.num + 1) % 3
        mes = __commit__(rMessage(res))  ####
        return mes.response


class FiveRecruie(Resource):
    def post(self):
        args = parser.parse_args()
        u_info = query(User).get(args['user_id'])
        if u_info is None:
            return rMessage(error=State.ArgError).response
        if u_info.money >= 400:
            u_info.money -= 400
        else:
            return rMessage(error=State.NoMoney).response  # no money
        res = getPlayer(u_info.id, 5)
        if isinstance(res, int):
            res = toPiece(u_info.id, res)
        items = [res]
        for i in range(4):
            items.append(getProp(u_info.id))
        mes = __commit__(rMessage(items))
        return mes.response


class RecruitPlayer(Resource):
    def post(self):
        args = parser.parse_args()
        user = query(User).get(args['user_id'])
        player = query(PlayerBase).get(args['player_id'])
        if (user is None) or (player is None):
            return rMessage(error=State.ArgError).response
        if user.money < player.price:
            return rMessage(error=State.NoMoney).response
        player_ids = getValidPlayer(user.id)
        if player.id in player_ids:
            return rMessage(error=State.OwnPlayer).response
        user.money -= player.price
        res = addPlayer(user.id, player)
        addPopular(player.id, 1)
        mes = __commit__(rMessage(res))  ####
        return mes.response


class ShowPlayer(Resource):
    def get(self):
        index = parser.parse_args()['order']##sort
        user_id = parser.parse_args()['user_id']
        pos = parser.parse_args()['pos']##filter
        if not index:
            index = 1
        if not pos:
            pos = 0
        if index not in range(-3,4) or pos not in range(6):
            return rMessage(error=State.ArgError).response
        order = [PlayerBase.id, PlayerBase.id, PlayerBase.score, PlayerBase.price]
        poss = ['','c','f','f','g','g']
        PB = PlayerBase
        res = query(PB.id,PB.name,PB.pos1,PB.pos2,PB.price,PB.score,PB.team_id)
        if pos != 0:
            res = res.filter((PB.pos1 == poss[pos]) | (PB.pos2 == poss[pos]))
        if abs(index)==1 and Recom.recom:
            pl = Recom.recom.sortRecommend(user_id)
            print('recom list')
            pinfo = {p[0]:p for p in res.all()}##id-tuple
            res = [pinfo[p] for p in pl if p in pinfo] ##tuple list
        else:
            res = res.order_by(db.desc(order[abs(index)])).all()
        if index <= 0:
            return rMessage([{"id": p[0], "name": p[1], "pos1": p[2], "pos2": p[3], "price": p[4],
                              "score": p[5]} for p in res]).response
        else:
            return rMessage([p[0] for p in res]).response


class BuyTheme(Resource):
    def post(self):
        args = parser.parse_args()
        theme = query(Theme).get(args['theme_id'])
        user = query(User).get(args['user_id'])
        if (user is None) or (theme is None):
            return rMessage(error=State.ArgError).response
        if user.money < theme.price:
            return rMessage(error=State.NoMoney).response
        user.money -= theme.price
        bag_players = getValidPlayer(user.id)
        res = list()
        for player_id in [theme.player_one_id, theme.player_two_id, theme.player_three_id]:
            addPopular(player_id, 0.5)
            if player_id in bag_players:
                data = toPiece(user.id, player_id)
            else:
                player = query(PlayerBase).get(player_id)
                data = addPlayer(user.id, player)
            res.append(data)
        mes = __commit__(rMessage(res))  ####
        return mes.response


class RenewContract(Resource):
    def __getInfo__(self):
        args = parser.parse_args()
        bag_player = query(BagPlayer).get(args['bag_player_id'])
        if bag_player is None:
            return None
        player = query(PlayerBase).get(bag_player.player_id)
        price = int(((bag_player.score * 1.0 / player.score) ** 2) * player.price)
        return [bag_player, price]

    def get(self):
        res = self.__getInfo__()
        if res is None:
            return rMessage(error=State.ArgError).response
        return rMessage({'price': res[1]}).response

    def post(self):
        res = self.__getInfo__()
        if res is None:
            return rMessage(error=State.ArgError).response
        bag_player = res[0]
        price = res[1]
        user = query(User).get(bag_player.user_id)
        if user.money < price:
            return rMessage(error=State.NoMoney).response
        else:
            user.money -= price
        bag_player.salary = price
        duedate = bag_player.duedate
        duedate = duedate.replace(year=duedate.year + 1)
        bag_player.duedate = duedate
        today = datetime.datetime.today()
        contract = '一年%d万，%d年%d月%d日续约，%d年%d月%d日到期' % (price, today.year,
                                                      today.month, today.day, duedate.year, duedate.month, duedate.day)
        bag_player.contract = contract
        addPopular(bag_player.player_id, 5)  ##add popular
        mes = __commit__(rMessage({'contract': contract}))
        return mes.response


class InitPlayer(Resource):
    def post(self):
        user_id = parser.parse_args()['user_id']
        c_player = selectPlayer(3, 'c')
        players = {choice(list(c_player))}
        f_player = selectPlayer(3, 'f') - players
        players.update(sample(list(f_player), 2))
        g_player = selectPlayer(3, 'g') - players
        players.update(sample(list(g_player), 2))
        res = list()
        for player_id in players:
            player = query(PlayerBase).get(player_id)
            res.append(addPlayer(user_id, player))
        mes = __commit__(rMessage(res))
        return mes.response


def addPopular(player_id, popular):
    po = query(PlayerStat).get(player_id)
    if not po:
        add(PlayerStat(player_id, 0, popular))
    else:
        po.popular = min(po.popular + popular, 100000000)


recruit_api.add_resource(GetRecruit, '/get_recruit_info')
recruit_api.add_resource(OneRecruit, '/one_recruit')
recruit_api.add_resource(FiveRecruie, '/five_recruit')
recruit_api.add_resource(RecruitPlayer, '/recruit')
recruit_api.add_resource(ShowPlayer, '/show_all_payer')
recruit_api.add_resource(BuyTheme, '/buy_theme')
recruit_api.add_resource(RenewContract, '/renew_contract')
recruit_api.add_resource(InitPlayer, '/init_player')


class Recom(Resource):
    recom = None

    def get(self):
        token = parser.parse_args()['user_id']
        kind = parser.parse_args()['order']
        if token != 923458897 or kind not in range(5):
            return rMessage("error").response
        if kind == 4:
            if Recom.recom:
                Recom.recom = None
                print('close recommendation system')
        else:
            if not Recom.recom:
                print('start init recommendation system, waiting ...')
                Recom.recom = Recommend()
                print('init successfully')
        if kind == 1:
            Recom.recom.genSim()##every three days,clear table
        if kind == 2:
            Recom.recom.genLikes()##once,clear table
        if kind == 3:
            Recom.recom.genMode()##every day

        return rMessage("finish").response


recruit_api.add_resource(Recom, '/manage_recom')
