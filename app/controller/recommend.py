from app import db
from app.model import PlayerBase, BagPlayer, BagTrailCard, BagPiece, Sim, PlayerStat, SeasonData, Like
from random import choice, random
import datetime,threading,time

query = db.session.query
add = db.session.add
add_all = db.session.add_all
delete = db.session.delete
commit = db.session.commit
rollback = db.session.rollback


def __commit__():
    try:
        commit()
        return True
    except Exception as e:
        rollback()
        print(e)
        return False


def __randomPick__(lists, prob):
    r = random()
    cum = 0.0
    for item, item_prob in zip(lists, prob):
        cum += item_prob
        if r < cum: break
    return item


class Recommend:
    def __init__(self):
        self.__sims = None  ##dict(dict())
        self.__likes = None  ##dict(dict())
        self.__mode = dict()
        self.__delInvalidPlayer__()
        self.__player_score = dict(query(PlayerBase.id, PlayerBase.score).all());
        items = query(Sim.player_one, Sim.player_two, Sim.sim).all()
        if not items:
            self.genSim()
            print('system first init sim')
        else:
            self.__getSim__(items)
            print('get sims')

            items = query(PlayerStat.player_id, PlayerStat.mode).all()
            self.__getMode__(items)
            print('get modes')

        items = query(Like.player_one, Like.player_two, Like.like).all()
        if not items:
            self.genLikes()
            print('system first init likes')
        else:
            self.__getLike__(items)
            print('get likes')

        player_id = BagPlayer.player_id
        self.__buyNum = query(player_id, db.func.count(player_id)).group_by(player_id).all()
        self.__threadAlive = True
        self.__thread = threading.Thread(target=self.watch)
        self.__thread.start()

    def __del__(self):
        self.__threadAlive = False
        self.__thread.join()
    ####team will win

    def genTrial(self, user_id):
        filter0 = query(BagPlayer.player_id, BagPlayer.score).filter(BagPlayer.user_id == user_id).all()
        filter1 = {i[0] for i in filter0}
        filter2 = query(BagTrailCard.player_id).filter(BagTrailCard.user_id == user_id).all()
        filter2 = {i[0] for i in filter2}
        if len([p for (p, s) in filter0 if s - self.__player_score[p] != 0]) > 10:  ##判断新老用户
            print('old user')
            players = self.__itemBased__(filter0, filter2)
        else:
            print('new user')
            players = self.__scoreBased__(filter1, filter2)
        if not players:
            print('cannot recom trial')
            return None
        if len(players) > 5:
            players = players[:5]
        player_id = choice(players)
        time_class = [1, 3, 5]
        prob = [0.85, 0.1, 0.05]
        time = __randomPick__(time_class, prob)
        return {"id": player_id, "time": time}

    def __scoreBased__(self, bp, tp):  ##众数法 O(P·ln(P))
        mp = {p for p in self.__mode}
        mp = mp - bp
        if mp - tp:
            mp = mp - tp
        if len(mp) < 1:
            return None
        pm = [(p, self.__mode[p]) for p in self.__mode if p in mp]
        pm = sorted(pm, key=lambda x: x[1], reverse=True) 
        return [p for (p, r) in pm]

    def __itemBased__(self, bps, tp):  ##项目协同 O(P^2)
        pl = self.__getLevelPlayer(bps) - {p for p, s in bps};
        if pl - tp:
            pl = pl - tp
        if len(pl) < 1:
            return None
        player_rate = [(p, s - self.__player_score[p]) for (p, s) in bps]
        rates = {p: 0 for p in pl}
        for p in pl:
            simsum = 0
            for (b, r) in player_rate:
                rates[p] += r * self.__sims[p][b]
                simsum += self.__sims[p][b]
            if simsum == 0:
                rates[p] = 0
            else:
                rates[p] /= simsum
        pl = sorted(rates.items(), key=lambda x: x[1], reverse=True) 
        return [p for (p, r) in pl]

    def __getLevelPlayer(self, bps):
        prob = [1] * 4
        for (p, s) in bps:
            if s < 70:
                prob[0] += 1
            if 70 <= s < 80:
                prob[1] += 1
            if 80 <= s < 90:
                prob[2] += 1
            if s >= 90:
                prob[3] += 1
        for i in range(len(prob)):
            prob[i] /= len(bps) + 4
        level = __randomPick__(range(4), prob)
        if level == 0:
            return {k for k, v in self.__player_score.items() if v < 70}
        if level == 1:
            return {k for k, v in self.__player_score.items() if 70 <= v < 80}
        if level == 2:
            return {k for k, v in self.__player_score.items() if 80 <= v < 90}
        if level == 3:
            return {k for k, v in self.__player_score.items() if v >= 90}

    def genSim(self):  ##O(P^2·U)  ok
        rates = self.calcRate()
        sims = dict()
        for p1 in rates:
            for p2 in rates:
                if p1==p2 or ((p1, p2) in sims) or ((p2, p1) in sims):
                    continue
                val = self.__cosDict__(rates[p1], rates[p2])
                if val:
                    sims[(p1, p2)] = val
        ####update sims
        query(Sim).delete()
        items = [(item[0], item[1], sims[item]) for item in sims]
        add_all([Sim(item[0], item[1], item[2]) for item in items])
        if __commit__():
            self.__getSim__(items)
            self.genMode(rates)

    def genMode(self, rates=None):  ##ok
        if rates is None:
            rates = self.calcRate()
        for item in query(PlayerStat).all():
            item.mode = 0
        for pd in {p for p in self.__player_score} - {i[0] for i in query(PlayerStat.player_id).all()}:
            add(PlayerStat(pd, 0, 0))
        modes = list()
        for player in rates:
            data = [0] * 11
            for user in rates[player]:
                data[int(rates[player][user])] += 1
            mode = data.index(max(data))
            modes.append((player, mode))
            query(PlayerStat).get(player).mode = mode
        if __commit__():
            items = query(PlayerStat.player_id, PlayerStat.mode).all()
            self.__getMode__(items)

    def calcRate(self):  ##O(U·P)  ##ok
        bag_players = query(BagPlayer.user_id, BagPlayer.player_id, BagPlayer.score).all()
        scores = self.__player_score
        rates = dict()
        rang = [100, 0]
        for item in bag_players:
            rate = item[2] - scores[item[1]]
            if rate == 0:
                continue
            rang[0] = min(rang[0], rate)
            rang[1] = max(rang[1], rate)
            if item[1] not in rates:
                rates[item[1]] = {item[0]: rate}
            else:
                rates[item[1]][item[0]] = rate
        for player in rates:
            for user in rates[player]:
                if rang[1] <= rang[0]:
                    rates[player][user] = 5
                else:
                    rates[player][user] = ((rates[player][user] - rang[0]) / (rang[1] - rang[0])) * 9 + 1
        return rates

    def __getSim__(self, items):
        players = self.__player_score.keys()
        self.__sims = {p1: {p2: 0 for p2 in players} for p1 in players}
        for (p1, p2, sim) in items:
            self.__sims[p1][p2] = sim
            self.__sims[p2][p1] = sim

    def __getMode__(self, items):
        for (p, m) in items:
            self.__mode[p] = m
        for pd in set(self.__player_score.keys()) - {i[0] for i in items}:  ##init every player_stat
            self.__mode[pd] = 0  ##every player has mode

    def __delInvalidPlayer__(self):
        now = datetime.datetime.now()
        query(BagPlayer).filter(BagPlayer.duedate <= now).delete()
        __commit__()

    def __cosDict__(self, v1, v2):  ##O(U)
        res1 = res2 = res3 = 0
        for u in v1:
            if u in v2:
                res1 += v1[u] * v2[u]
            res2 += v1[u] ** 2
        for u in v2:
            res3 += v2[u] ** 2
        if res2 * res3 == 0:
            return None
        return res1 / ((res2 * res3) ** 0.5)

    ####user would like
    def sortRecommend(self, user_id):
        bp = query(BagPlayer.player_id).filter(BagPlayer.user_id == user_id).all()
        if len(bp) > 20:  ##判断新老用户
            return self.__contentBased__(user_id, bp)
        else:
            return self.__popularBased__()

    def __contentBased__(self, user_id,bp):  ##O(P^2)
        bag_players = {i[0] for i in bp}
        trial_players = query(BagTrailCard.player_id).filter(BagTrailCard.user_id == user_id).all()
        trial_players = {i[0] for i in trial_players}
        piece_players = query(BagPiece.player_id).filter(BagPiece.user_id == user_id).all()
        piece_players = {i[0] for i in piece_players}
        players = list()
        for player in {p for p in self.__player_score} - bag_players:
            score = 0
            for bp in bag_players:
                ps = self.__player_score[player]
                bps = self.__player_score[bp]
                like = self.__likes[player][bp]
                if bps > ps and bps < ps + 5 and like > 0.6:
                    like = like * 5
                score += like
            if player in trial_players:
                score = score * 1.2
            if player in piece_players:
                score = score * 0.8
            players.append((player, score))
        for player in bag_players:
            players.append((player, 0))
        players = sorted(players, key=lambda x: x[1], reverse=True)
        return [p for (p, s) in players]

    def __popularBased__(self):
        pp = dict(query(PlayerStat.player_id, PlayerStat.popular).all())
        ppo = list()
        for p in {p for p in self.__player_score}:
            if p not in pp:
                pp[p] = 0
            ppo.append((p, pp[p]))
        ppo = sorted(ppo, key=lambda x: x[1], reverse=True)
        return [p for (p, po) in ppo]

    def genLikes(self):  ##ok
        s = SeasonData
        players = query(s.player_id, s.gp, s.min, s.reb, s.fg_pct, s.fg3_pct, s.ft_pct, s.pts, s.ast, s.oreb, s.dreb,
                        s.stl, s.blk,
                        s.tov, s.fgm, s.fga, s.fg3m, s.efg_pct, s.ts_pct, s.ortg, s.drtg).all()
        likes = dict()
        for p1 in players:
            for p2 in players:
                if ((p1, p2) in likes) or ((p2, p1) in likes):
                    continue
                val = self.__cosList__(p1[1:], p2[1:])
                likes[(p1[0], p2[0])] = val
        ####update likes
        query(Like).delete()
        items = [(item[0], item[1], likes[item]) for item in likes]
        add_all([Like(item[0], item[1], item[2]) for item in items])
        if __commit__():
            self.__getLike__(items)

    def __getLike__(self, items):
        players = self.__player_score.keys()
        self.__likes = {p1: {p2: 0 for p2 in players} for p1 in players}
        for (p1, p2, like) in items:
            self.__likes[p1][p2] = like
            self.__likes[p2][p1] = like

    def __cosList__(self, v1, v2):  ##O(U) ok
        res1 = res2 = res3 = 0
        if len(v1) != len(v2):
            return None
        for i in range(len(v1)):
            res1 += v1[i] * v2[i]
            res2 += v1[i] ** 2
            res3 += v2[i] ** 2
        if res2 * res3 == 0:
            return 0
        return res1 / ((res2 * res3) ** 0.5)

    ####optimize
    def genPiece(self):  ####ok
        old_players = {p[0] for p in self.__buyNum}
        all_players = {p for p in self.__player_score}
        players = list(all_players - old_players)
        if not players:
            players = sorted(self.__buyNum, key=lambda x: x[1]) 
            players = [p for (p, c) in players]
            if len(players) > 10:
                players = players[:10]
        player_id = choice(players)
        num_class = [1, 5, 10, 15]
        prob = [0.45, 0.4, 0.1, 0.05]
        num = __randomPick__(num_class, prob)
        return {"id": player_id, "num": num}


    def watch(self):
        print('watch run')
        sTime = datetime.datetime.now()
        mTime = datetime.datetime.now()
        pTime = datetime.datetime.now()
        while self.__threadAlive:
            cTime = datetime.datetime.now()
            if cTime-sTime >= datetime.timedelta(days=3):
                self.genSim()
                sTime = cTime
                print('auto gen sim')
            else:
                if cTime-mTime >= datetime.timedelta(days=1):
                    self.genMode()
                    mTime = cTime
                    print('auto gen mode')
            if cTime-pTime >= datetime.timedelta(seconds=28800):
                player_id = BagPlayer.player_id
                self.__buyNum = query(player_id, db.func.count(player_id)).group_by(player_id).all()
                pTime = cTime
                print('auto gen piece')
            time.sleep(28800)