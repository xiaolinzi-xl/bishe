from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, MasterDetailView
from app import appbuilder, db
from app.model import Equip, AttrCh, OStrategy, DStrategy, FundType, Theme
"""
    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(MyModelView, "My View", icon="fa-folder-open-o", category="My Category", category_icon='fa-envelope')
"""
class FundTypeModelView(ModelView):
    datamodel = SQLAInterface(FundType)
    list_columns = [
        'price', 'rate'
    ]
class ThemeModelView(ModelView):
    datamodel = SQLAInterface(Theme)
    list_columns = [
        'title', 'price'
    ]
    show_fieldsets = [
        ('Base',{'fields':[
            'title', 'detail', 'price'
        ]}),
        ('Players',{'fields':[
            'player_one','player_two','player_three'
        ]})
    ]
    add_fieldsets = [
        ('Base',{'fields':[
            'title', 'detail', 'price'
        ]}),
        ('Players',{'fields':[
            'player_one','player_two','player_three'
        ]})
    ]
class AttrChModelView(ModelView):
    datamodel = SQLAInterface(AttrCh)
    
    

class EquipModelView(ModelView):
    datamodel = SQLAInterface(Equip)
    list_columns = [
        'name', 'attr_ch.comment'
    ]
    #related_views = [AttrChModelView]
    show_fieldsets = [
        ('Base',{'fields':['name','attr_ch'],'expanded':True}),
        ('Detail',{'fields':[
            'attr_ch.order',
            'attr_ch.fg_pct','attr_ch.three_pt_pct','attr_ch.fta_pct',
            'attr_ch.oreb_pct','attr_ch.dreb_pct','attr_ch.ast_pct',
            'attr_ch.tov_pct','attr_ch.stl_pct','attr_ch.blk_pct',
            'attr_ch.pf_pct',
            ]})
    ]
    edit_fieldsets = [
        ('Base',{'fields':['name','attr_ch'],'expanded':True})
    ]

class OStrategyModelView(ModelView):
    datamodel = SQLAInterface(OStrategy)
    list_columns = [
        'intro'
    ]
    show_fieldsets = [
        ('Base',{'fields':['intro'],'expanded':True}),
        ('Detail',{'fields':[
            'sg.order',
            'sg','sg.fg_pct','sg.three_pt_pct','sg.fta_pct',
             'sg.oreb_pct','sg.dreb_pct','sg.ast_pct',
            'sg.tov_pct','sg.stl_pct','sg.blk_pct',
             'sg.pf_pct',
             'sf','sg.fg_pct','sf.three_pt_pct','sf.fta_pct',
             'sf.oreb_pct','sf.dreb_pct','sf.ast_pct',
            'sf.tov_pct','sf.stl_pct','sf.blk_pct',
             'sf.pf_pct',
             'pg','pg.fg_pct','pg.three_pt_pct','pg.fta_pct',
             'pg.oreb_pct','pg.dreb_pct','pg.ast_pct',
            'pg.tov_pct','pg.stl_pct','pg.blk_pct',
             'pg.pf_pct',
             'pf','pf.fg_pct','pf.three_pt_pct','pf.fta_pct',
             'pf.oreb_pct','pf.dreb_pct','pf.ast_pct',
            'pf.tov_pct','pf.stl_pct','pf.blk_pct',
             'pf.pf_pct',
             'c','c.fg_pct','c.three_pt_pct','c.fta_pct',
             'c.oreb_pct','c.dreb_pct','c.ast_pct',
            'c.tov_pct','c.stl_pct','c.blk_pct',
             'c.pf_pct'
            ]})
    ]
    add_fieldsets = [
        ('Base',{'fields':[
            'intro', 'sg','sf','pg','pf','c'
        ]})
    ]
    edit_fieldsets = [
        ('Base',{'fields':[
            'intro', 'sg','sf','pg','pf','c'
        ]})
    ]

class DStrategyModelView(ModelView):
    datamodel = SQLAInterface(DStrategy)
    list_columns = [
        'intro'
    ]
    show_fieldsets = [
        ('Base',{'fields':['intro'],'expanded':True}),
        ('Detail',{'fields':[
            'sg.order',
            'sg','sg.fg_pct','sg.three_pt_pct','sg.fta_pct',
             'sg.oreb_pct','sg.dreb_pct','sg.ast_pct',
            'sg.tov_pct','sg.stl_pct','sg.blk_pct',
             'sg.pf_pct',
             'sf','sg.fg_pct','sf.three_pt_pct','sf.fta_pct',
             'sf.oreb_pct','sf.dreb_pct','sf.ast_pct',
            'sf.tov_pct','sf.stl_pct','sf.blk_pct',
             'sf.pf_pct',
             'pg','pg.fg_pct','pg.three_pt_pct','pg.fta_pct',
             'pg.oreb_pct','pg.dreb_pct','pg.ast_pct',
            'pg.tov_pct','pg.stl_pct','pg.blk_pct',
             'pg.pf_pct',
             'pf','pf.fg_pct','pf.three_pt_pct','pf.fta_pct',
             'pf.oreb_pct','pf.dreb_pct','pf.ast_pct',
            'pf.tov_pct','pf.stl_pct','pf.blk_pct',
             'pf.pf_pct',
             'c','c.fg_pct','c.three_pt_pct','c.fta_pct',
             'c.oreb_pct','c.dreb_pct','c.ast_pct',
            'c.tov_pct','c.stl_pct','c.blk_pct',
             'c.pf_pct'
            ]})
    ]
    add_fieldsets = [
        ('Base',{'fields':[
            'intro', 'sg','sf','pg','pf','c'
        ]})
    ]
    edit_fieldsets = [
        ('Base',{'fields':[
            'intro', 'sg','sf','pg','pf','c'
        ]})
    ]




