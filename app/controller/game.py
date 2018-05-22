from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource,reqparse
from app.model import User, UserGame, LineUp, BagPlayer, UserMatch, InputData, OStrategy, DStrategy
from app import db, _jpush, jpush
import threading
import time
from .message import Message
from collections import defaultdict
from .user import UserError,Auth
from math import pow, log10
from queue import Queue
import datetime
import json
from .utils import Verify

game_bp = Blueprint('game_bp', __name__, static_folder="../static/game")
game_api = Api(game_bp)


class GameError:
    GAME_FAILED = 'game failed', -701
    RESULT_SENDED = 'result sended', -702
    NO_RESULT = 'no result', -703

class GameMessage(Message):
    GAMING = 'Gaming'
    MATCHING = 'Matching'
    DONE = 'Done'
    ERROR = 'Error'
    MATCHED = 'Matched'

    def __init__(self,result = None, error='', state=0):
        super(GameMessage,self).__init__(result,error,state)
    @property
    def gaming(self):
        self.add('result',self.GAMING)
        return self
    @property
    def matching(self):
        self.add('result',self.MATCHING)
        return self

class GameResult:
    __colNames = (
        'pts', 'oreb', 'dreb','ast','stl','blk','in_pts','tov','ft','three_pt'
    )
    __colNames_zh = (
        '得分', '进攻篮板','防守篮板','助攻','抢断','盖帽','内线得分','失误','罚球','三分球'
    )
    
    def __init__(self,pts=0,oreb=0,dreb=0,ast=0,stl=0,blk=0,in_pts=0,tov=0,ft=0,three_pt=0):
        self.__result = dict(
            {'pts':pts, 'oreb':oreb,'dreb':dreb,'ast':ast,'stl':stl,
            'blk':blk,'in_pts':in_pts, 'tov':tov,'ft':ft,'three_pt':three_pt}
        )
    @property
    def result(self):
        return self.__result

    def toJson(self):
        return json.dumps(
            {
                self.__colNames_zh[index]:self.__result[self.__colNames[index]] for index in range(len(self.__colNames))
            }
        )

class Rank:
    p = 0.618
    k = 400*log10(p/(1-p))/5*2
    d = 1000
    def __init__(self):
        # scores = db.session.query(UserMatch.user_id, UserMatch.score).all()
        # self.scores = {row[0]:row[1] for row in scores}
        self.scores = {}
    @staticmethod
    def ELO( ra, rb, sa):
        ea = 1/(1+pow(10,-(ra-rb)/400))
        eb = 1-ea
        new_ra = ra + Rank.k*(sa-ea)
        new_rb = rb + Rank.k*(1-sa-eb)
        return new_ra, new_rb
    def __rank(self, score):
        r = (score - self.d) // self.k
        return r if r >= 0 else 0
    def __call__(self,user):
        userMatch = UserMatch.query.filter_by(user_id = user.id).first()
        self.scores[user.id] = userMatch.score
        return self.__rank(self.scores[user.id])
    
    def update(self, user,new_score):
        userMatch = UserMatch.query.filter_by(user_id=user.id).first()
        if userMatch is None:
            userMatch = UserMatch(user.id)
            db.session.add(userMatch)
            db.session.commit()
            #userMatch = UserMatch.query.filter_by(user_id=user.id).first()
        userMatch.score = new_score
        db.session.add(userMatch)
        db.session.commit()
        self.scores[user.id] = new_score  

class GlobalVar:
    matchers = defaultdict(lambda : Queue(-1))
    userStates = defaultdict(lambda : None)
    tasks = Queue(-1)
    lineups = {}
    rank = Rank()
    gameRooms = {}

class GameInputData:
    __colNames = (
        'pts', 'fg_pct','three_pt_pct', 'fta', 'oreb_pct',
        'dreb_pct', 'ast_pct', 'tov', 'stl','blk','pf','p_m'
    )
    def __init__(self, input_data):
        
        self.__result = {
            colName : getattr(input_data,colName) for colName in self.__colNames
        }
    def updateAttr(self, attr):
        not_in = ('pts','p_m')
        not_pct = ('fta','tov','stl','blk','pf')
        for colName in self.__colNames:
            if colName not in not_in:
                if colName in not_pct:
                    self.__result[colName] *= 1+ getattr(attr,colName)
                else:
                    self.__result[colName] += getattr(attr,colName)
    

def net(players1,players2):
    '''
        players : {pos:GameInputData}
    '''
    return GameResult(), GameResult()

    

class GameThread(threading.Thread):
    def __init__(self, matcher1, matcher2):
        threading.Thread.__init__(self)
        self.matcher1 = matcher1
        self.matcher2 = matcher2
        self.lineup1 = LineUp.query.filter_by(id=GlobalVar.lineups[self.matcher1.user.id]).first()
        self.lineup2 = LineUp.query.filter_by(id=GlobalVar.lineups[self.matcher2.user.id]).first()
        self.pos = ['sf','sg','c','pf','pg']
        self.lineup1_input_data = self.getInputData(self.lineup1)
        self.lineup2_input_data = self.getInputData(self.lineup2)
       
        self.addStrategyAttr(self.lineup1, self.lineup1_input_data, self.lineup2_input_data)
        self.addStrategyAttr(self.lineup2, self.lineup2_input_data, self.lineup1_input_data)
        
    def getInputData(self, lineup):
        return {pos:GameInputData(input_data) 
            for pos, input_data in zip(self.pos,
                [InputData.query.filter_by(
                    player_base_id = BagPlayer.query.get(getattr(lineup, ppos)).player_id).first()
                    for ppos in self.pos
                ])}
    def addStrategyAttr(self, lineup, my_input_data, other_input_data):
        ostrategy = OStrategy.query.filter_by(id = lineup.ostrategy_id).first()
        dstrategy = DStrategy.query.filter_by(id = lineup.dstrategy_id).first()
        if ostrategy is not None:
            for pos in self.pos:
                attr = getattr(ostrategy,pos)
                data = my_input_data[pos]
                data.updateAttr(attr)
        if dstrategy is not None:
            for pos in self.pos:
                attr =getattr(dstrategy, pos)
                data = other_input_data[pos]
                data.updateAttr(attr)
    def mainGame(self):
        '''
        net : 
        '''
        player1Res, player2Res = net(self.lineup1_input_data, self.lineup2_input_data)
        return player1Res, player2Res
    def writeResult(self, player1Res, player2Res):
        matcher1 = self.matcher1
        matcher2 = self.matcher2
        sa = 1 if player1Res.result['pts'] > player2Res.result['pts'] else 0.5 if player1Res.result['pts'] == player2Res.result['pts'] else 0
        new_score1, new_score2 = GlobalVar.rank.ELO(matcher1.rank,matcher2.rank,sa)
        GlobalVar.tasks.put(UpdateScoreTask(matcher1.user,new_score1))
        GlobalVar.tasks.put(UpdateScoreTask(matcher2.user,new_score2))
        userGame1 = UserGame(matcher1.user.id, datetime.datetime.today(),**(player1Res.result))
        userGame2 = UserGame(matcher1.user.id, datetime.datetime.today(),**player2Res.result)
        db.session.add(userGame1)
        db.session.add(userGame2)
        db.session.commit()
        
    def run(self):
        player1Res, player2Res = self.mainGame()
        self.writeResult(player1Res, player2Res)
        SendResultTask(self.matcher1.user.id, self.matcher2.user.id,player1Res, player2Res).run()
        GlobalVar.tasks.put(ModifyStateTask(str(self.matcher1),GameMessage.DONE))
        GlobalVar.tasks.put(ModifyStateTask(str(self.matcher2),GameMessage.DONE))
        
  

class ProcessTasksThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global GlobalVar
        while True:
            task = GlobalVar.tasks.get()
            task.run()
            GlobalVar.tasks.task_done()

class MatchThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global GlobalVar
        while True:
            for _, matchers in GlobalVar.matchers.items():
                start_time = time.time()
                if matchers.qsize() >= 2:
                    while matchers.qsize() > 1 and time.time() - start_time < 2:
                        matcher1 = matchers.get()
                        matchers.task_done()
                        matcher2 = matchers.get()
                        matchers.task_done()
                        GlobalVar.tasks.put(SendMatchedTask(matcher1.user.id, matcher2.user.id))
                        GlobalVar.tasks.put(ModifyStateTask(str(matcher1),GameMessage.GAMING))
                        GlobalVar.tasks.put(ModifyStateTask(str(matcher2),GameMessage.GAMING))
                        GlobalVar.tasks.put(GameTask(matcher1,matcher2))
            time.sleep(2)

class Matcher:
    MIN_RANK = 0
    MAX_RANK = 10
    def __init__(self,user):
        self.__rank = GlobalVar.rank(user)
        self.__time = time.time()
        self.__user = user

    def __getRange(self):
        currTime = time.time()
        due = int(currTime - self.__time) // 10
        return max(self.__rank-due, self.MIN_RANK) , min(self.__rank+due, self.MAX_RANK)
    def can(self, rank):
        range = self.__getRange()
        return rank >= range[0] and rank  <= range[1]
    @property
    def rank(self):
        return self.__rank
    def __str__(self):
        return str(self.__user)
    @property
    def user(self):
        return self.__user
def sendMessage(message,users):
    push = _jpush.create_push()
    push.platform = jpush.all_
    alias = {'alias':
        [user for user in users]
    }
    push.audience = jpush.audience(alias)
    push.message = jpush.message('content',extras=message)
    push.send()
class GameLineUp:
    __pos = ('sf','sg','c','pf','pg')
    def __init__(self,lineup_id):
        self.__lineup = LineUp.query.filter_by(id = lineup_id).first()
    @property
    def lineup(self):
        return self.__lineup
    def getPlayerIdNames(self):
        names = []
        ids = []
        for pos in self.__pos:
            bagPlayer = BagPlayer.query.filter_by(id = getattr(self.__lineup, pos)).first()
            names.append(bagPlayer.player.name)
            ids.append(bagPlayer.player.id)
        return {id:name for id, name in zip(ids,names)}
    @property
    def json(self):
        res = self.getPlayerIdNames()
        return json.dumps(res)

class Task:
    def __init__(self):
        pass
    def run(self):
        pass
class SendMatchedTask(Task):
    def __init__(self, user1_id, user2_id):
        self.user1_id = user1_id
        self.user2_id = user2_id
    def run(self):
        '''
        message : MATCHED and linueup
        '''
        message = {
            'matched':GameMessage.MATCHED,
            str(self.user1_id):GameLineUp(GlobalVar.lineups[self.user1_id]).json,
            str(self.user2_id):GameLineUp(GlobalVar.lineups[self.user2_id]).json
        }
        sendMessage(message,[str(self.user1_id), str(self.user2_id)])
        
class ModifyStateTask(Task):
    
    def __init__(self, user_str, new_state):
        self.user_str = user_str
        self.state = new_state
    def run(self):
        GlobalVar.userStates[self.user_str] = self.state
class AddInMatchersTask(Task):
    def __init__(self, user):
        self.user = user
    def run(self):
        matcher = Matcher(self.user)
        GlobalVar.matchers[matcher.rank].put(matcher)   #[matcher.rank].append(matcher)
class GameTask(Task):
    def __init__(self,matcher1, matcher2):
        self.matcher1 = matcher1
        self.matcher2 = matcher2
    def run(self):
        gameThread = GameThread(self.matcher1, self.matcher2)
        gameThread.start()
class ModifyLineupTask(Task):
    def __init__(self, user_id, lineup_id):
        self.user_id = user_id
        self.lineup_id = lineup_id
    def run(self):
        GlobalVar.lineups[self.user_id] = self.lineup_id
class UpdateScoreTask(Task):
    def __init__(self,user, new_score):
        self.user = user
        self.new_score = new_score    
    def run(self):
        GlobalVar.rank.update(self.user, self.new_score)   
class AddInGameRoomTask(Task):
    def __init__(self, matcher1, matcher2):
        self.matcher1 = matcher1
        self.matcher2 = matcher2
    def run(self):
        GlobalVar.gameRooms[str(self.matcher1)] = self.matcher2
        GlobalVar.gameRooms[str(self.matcher2)] = self.matcher1
class DelGameRoomTask(Task):
    def __init__(self, matcher1, matcher2):
        self.matcher1 = matcher1
        self.matcher2 = matcher2
    def run(self):
        del GlobalVar.gameRooms[str(self.matcher1)]
        del GlobalVar.gameRooms[str(self.matcher2)]
class SendResultTask(Task):
    def __init__(self, user1_id, user2_id, game1Result, game2Result):
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.game1Result = game1Result
        self.game2Result = game2Result
    def run(self):
        push = _jpush.create_push()
        alias = {'alias':[str(self.user1_id),str(self.user2_id)]}
        push.audience = jpush.audience(alias)
        push.message = jpush.message(
            'content',extras = {
                str(self.user1_id):self.game1Result.toJson(),
                str(self.user2_id):self.game2Result.toJson()
            }
        )
        push.platform = jpush.all_
        push.send()

class GameApi(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('user_id',type=int)
    parser.add_argument('lineup_id',type=int)
    def post(self):
        global GlobalVar
        args = self.parser.parse_args(strict=True)
        user_id = args['user_id']
        lineup_id = args['lineup_id']
        if not lineup_id or not user_id:
            return GameMessage(None, *GameError.GAME_FAILED).response
        #print(LineUp.query.get(lineup_id))
        if LineUp.query.get(lineup_id) is None:
            return GameMessage(None, *GameError.GAME_FAILED).response

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return GameMessage(None,*UserError.ILLEGAL_USER).response
        userState = GlobalVar.userStates[str(user)]
        if userState is None or userState == GameMessage.DONE:
            GlobalVar.tasks.put(ModifyStateTask(str(user),GameMessage.MATCHING))
            GlobalVar.tasks.put(ModifyLineupTask(user_id,lineup_id))
            GlobalVar.tasks.put(AddInMatchersTask(user))
            return GameMessage().matching.response
        return GameMessage(None, *GameError.NO_RESULT).response
        

class FriendGame(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('user_id',type=int)
    parser.add_argument('friend_id',type=int)
    def post(self):
        self.parser.add_argument('lineup_id',type=int)
        args = self.parser.parse_args(strict=True)
        user_id = args['user_id']
        friend_id = args['friend_id']
        lineup_id = args['lineup_id']
        user = Verify.verifyUser(user_id)
        friend = Verify.verifyUser(friend_id)
        if not user or not friend:
            return GameMessage(None,*UserError.ILLEGAL_USER).response
        message = GameMessage({
            'content':'friend game',
            'from':user_id,
            'from_nickname':user.nickname
            },state=700).data
        sendMessage(message,[str(friend_id)])
        GlobalVar.tasks.put(ModifyLineupTask(user_id,lineup_id))
        return GameMessage('waiting',state=700)
    def delete(self):
        args = self.parser.parse_args(strict=True)
        user_id = args['user_id']
        friend_id = args['friend_id']
        user = User.query.filter_by(id=user_id).first()
        friend = User.query.filter_by(id=friend_id).first()
        if not user or not friend:
            return GameMessage(None,*UserError.ILLEGAL_USER).response
        message = GameMessage({
            'content':'reject friend game',
            'from':user_id,
            'from_nickname':user.nickname
        },state=700).data
        sendMessage(message,[str(friend_id)])
        return GameMessage('',state=700)
    def get(self):
        self.parser.add_argument('lineup_id',type=int)
        args = self.parser.parse_args(strict=True)
        user_id = args['user_id']
        friend_id = args['friend_id']
        lineup_id = args['lineup_id']
        user = User.query.filter_by(id=user_id).first()
        friend = User.query.filter_by(id=friend_id).first()
        if not user or not friend:
            return GameMessage(None,*UserError.ILLEGAL_USER).response
        message = GameMessage({
            'content':'accept friend game',
            'from':user_id,
            'from_nickname':user.nickname
        }).data
        sendMessage(message,[str(friend_id)])
        GlobalVar.tasks.put(ModifyLineupTask(user_id,lineup_id))
        GlobalVar.tasks.put(ModifyStateTask(str(user),GameMessage.GAMING))
        GlobalVar.tasks.put(ModifyStateTask(str(friend),GameMessage.GAMING))
        GlobalVar.tasks.put(GameTask(Matcher(user),Matcher(friend)))
        return GameMessage(GameMessage.GAMING,state=700).response

       
game_api.add_resource(GameApi,'/game')
game_api.add_resource(FriendGame,'/friendgame')

matchThread = MatchThread()
matchThread.setDaemon(True)
processTaskThread = ProcessTasksThread()
processTaskThread.setDaemon(True)

matchThread.start()
processTaskThread.start()


        
