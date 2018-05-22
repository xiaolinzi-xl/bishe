from flask_appbuilder import IndexView

class MyIndexView(IndexView):
    route_base = '/ibg'
    index_template = 'index.html'