from flask import Blueprint, jsonify, request, abort
from flask_restful import Api, Resource
from app.model import Theme, VipCard, User, Vip, Fund, FundType, PlayerBase
from app.controller import Message
from app import db
from datetime import datetime, timedelta, date
from sqlalchemy.exc import IntegrityError

activity_bp = Blueprint('activity_bp', __name__)
activity_api = Api(activity_bp)

query = db.session.query

# your code
class apiForTheme(Resource):
	def get(self):
		if 'themeId' in request.args:
			# get info of the three players in themeId
			themeId = request.args['themeId']
			try:
				theme = query(Theme).filter_by(id=themeId).first()
				data = list()
				players = [theme.player_one_id, theme.player_two_id, theme.player_three_id]
				for index in range(3):
					player = query(PlayerBase).filter_by(id=players[index]).first()
					birthday = datetime(year=player.birthday.year, month=player.birthday.month, day=player.birthday.day)
					ageInDays = (datetime.now() - birthday).days
					ageInYears = ageInDays // 365
					data.append({'name':player.name, 'age':ageInYears, 'price':player.price, 'score':player.score})
				return Message(data).response
			except:
				return Message(error='Database Query Error', state=-1).response
		else: 
			# when there is not args in request, return list of all themes
			rows = list()
			try:
				rows = query(Theme).all()
			except:
				mes = Message(error='Database Query Error', state=-1)
				return mes.response
			data = list()
			for row in rows:
				data.append({'id':row.id, 'title':row.title, 'detail':row.detail, 'price':row.price, 
				'player_one':row.player_one_id, 'player_two':row.player_two_id, 'player_three':row.player_three_id})
			return Message(data).response

class apiForVip(Resource):
	card_type = ['week','month','year','permanent']
	duration = [7,30,365,9999]

	def get(self):
		if 'userId' in request.args:
			# get VIP level of userId
			userId = request.args['userId']
			try:
				vipLevel = query(Vip).filter_by(user_id=userId).first().level
				return Message(vipLevel).response
			except:
				return Message(error='Database Query Error', state=-1).response
		else:
			# get prices of all four types of vip
			res = dict()
			for card in self.card_type:
				index = self.card_type.index(card)
				try:		
					res[card] = query(VipCard).filter_by(time = self.duration[index]).first().price
				except:
					return Message(error='Database Query Error', state=-1).response
			return Message(res).response
		
	def post(self):
		# userId buys vipType

		if 'userId' not in  request.form or 'vipType' not in request.form:
			return Message(error='Args Type Error',state=-1).response

		userId = request.form['userId'] 
		vipType = request.form['vipType']
		# print('type of userId: ' + str(type(userId)) + ', value: ' + str(userId))
		# print('type of vipType: ' + str(type(vipType)) + ', value: ' + str(userId))

		# check if vipType is valid
		if_vipType_exists = False
		for card in self.card_type:
			if vipType == card:
				if_vipType_exists = True
		if not if_vipType_exists:
			return Message(error='Arg Error: vipType does not exist in Database', state=-1).response

		# check if userId exists in table User
		try:				
			if_userId_exists_in_user = False if len(query(User).filter_by(id = userId).all()) == 0 else True
			if not if_userId_exists_in_user:
				return Message(error='Arg Error: userId does not exist in Database', state=-1).response
		except:
			return Message(error='Database Query Error', state=-1).response

		# check if userId has enough money
		try:
			index = self.card_type.index(vipType)
			money_left = query(User).filter_by(id = userId).first().money
			money_needed = query(VipCard).filter_by(time = self.duration[index]).first().price
		except:
			return Message(error='Database Query Error', state=-1).response
		if money_left <= money_needed:
			return Message(error='Not enough money in account', state=-1).response
		
		# update userId's money in account
		try:
			this_user = query(User).filter_by(id = userId).first()
			this_user.money -= money_needed
			# db.session.commit()
		except:
			return Message(error='Database Update Error', state=-1).response

		# check if userId exists in table Vip, compute the next duedate
		time_delta = timedelta(days = self.duration[self.card_type.index(vipType)])
		if_userId_exists_in_vip = False if len(query(Vip).filter_by(user_id = userId).all()) == 0 else True
		duedate_before = query(Vip).filter_by(user_id = userId).first().duedate if if_userId_exists_in_vip else datetime.now()
		duedate_after = duedate_before + time_delta
		if if_userId_exists_in_vip:
			try:
				row = query(Vip).filter_by(user_id = userId).first()
				row.duedate = duedate_after
				db.session.commit()
			except:
				return Message(error='Database Update Error', state=-1).response
		else:
			row = Vip(user_id = userId, level = 1, active = True, duedate = duedate_after)
			try:
				db.session.add(row)
				db.session.commit()
			except:
				return Message(error='Database Insert Error', state=-1).response
		return Message().response
		# TODO: what if updating money succeeds but prolonging duedate failed? how to implement rollback here?

class apiForFinance(Resource):
	def get(self):
		# get all finance products
		try:
			rows = query(FundType).all()
		except:
			return Message(error='Database Query Error', state=-1).response
		data = list()
		for row in rows:
			data.append({'id':row.id, 'price':row.price, 'rate': row.rate})
		return Message(data).response
	
	def post(self):
	 	# userId buys a financeType
		if 'userId' not in  request.form or 'financeType' not in request.form:
			return Message(error='Args Type Error',state=-1).response

		userId = request.form['userId']
		financeType = request.form['financeType']
		
		# check if userId exists in table User
		try:
			if_userId_exists_in_user = False if len(query(User).filter_by(id = userId).all()) == 0 else True
			if not if_userId_exists_in_user:
				return Message(error='Arg Error: userId does not exist in Database', state=-1).response
		except:
			return Message(error='Database Query Error', state=-1).response

		# check if financeType exists in table fund_type
		try:
			if_financeType_exists_in_fund_type = False if len(query(FundType).filter_by(id = financeType).all()) == 0 else True
			if not if_financeType_exists_in_fund_type:
				return Message(error='Arg Error: financeType does not exist in Database', state=-1).response
		except:
			return Message(error='Database Query Error', state=-1).response

		# userId buys financeType
		# check if userId has enough money
		try:
			money_left = query(User).filter_by(id = userId).first().money
			money_needed = query(FundType).filter_by(id = financeType).first().price
		except:
			return Message(error='Database Query Error', state=-1).response
		if money_left <= money_needed:
			return Message(error='Not enough money in account', state=-1).response
		# update userId's money in account
		try:
			this_user = query(User).filter_by(id = userId).first()
			this_user.money -= money_needed
			# db.session.commit()
			# later commit() is better, since the transcation includes other operations
		except:
			return Message(error='Database Update Error', state=-1).response
		# insert into table fund
		row = Fund(user_id = userId, fund_type_id = financeType)
		try:
			db.session.add(row)
			db.session.commit()
		except:
			return Message(error='Database Insert Error', state=-1).response
		return Message().response



activity_api.add_resource(apiForTheme, '/theme')
activity_api.add_resource(apiForVip, '/vip')
activity_api.add_resource(apiForFinance, '/finance')
