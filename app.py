from flask import Flask, render_template, request, redirect, json, jsonify, abort
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///singapore_daily.db'
db = SQLAlchemy(app)
api = Api(app)
ma = Marshmallow(app)


class CaseModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    country_region = db.Column(db.String(200), nullable=False)
    confirmed = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    recovered = db.Column(db.Integer)
    active = db.Column(db.Integer)

    def __repr__(self):
        return "<CaseModel {'id':%s, 'date':%s, 'country_region':%s, 'confirmed':%s, 'deaths':%s}>" % (self.id, self.date, self.country_region, self.confirmed, self.deaths)

# Multiple Day Case Schema
class CaseSchema(ma.Schema):
  class Meta:
    fields = ('id', 'date', 'country_region', 'confirmed', 'deaths', 'recovered', 'active')

# Single Day Case Schema
class DailySchema(ma.Schema):
  class Meta:
    fields = ('date', 'confirmed', 'deaths', 'recovered', 'active')

# Init schema
daily_schema = DailySchema()
case_schema = CaseSchema(many=True)

# Some python scheduler to update db cron?

class CountAll(Resource):
    def get(self, country):
        exists = CaseModel.query.filter(CaseModel.country_region.ilike(country)).first()
        if not exists:
            print(country + " does not exist")
            abort(404, description="Resource not found")
        else:
            cases = CaseModel.query.filter_by(country_region=country).order_by(CaseModel.date.desc()).all()
            result = case_schema.dump(cases)
            # Modify the date here (for loop)
            print(result)
            return jsonify(result)  

class CountLatest(Resource):
    def get(self, country):
        exists = CaseModel.query.filter(CaseModel.country_region.ilike(country)).first()
        if not exists:
            print(country + " does not exist")
            abort(404, description="Resource not found")
        else:
            current = CaseModel.query.filter_by(country_region=country).order_by(CaseModel.date.desc()).first()
            current = daily_schema.dump(current)
            current_date = datetime.strptime(current['date'].split('T')[0], '%Y-%m-%d').date()
            total_cases = current['confirmed']
            total_deaths = current['deaths']

            previous = CaseModel.query.filter_by(country_region=country).filter(CaseModel.date < current_date).order_by(CaseModel.date.desc()).first()
            previous = daily_schema.dump(previous)
            new_cases = total_cases - previous['confirmed']
            new_deaths = total_deaths - previous['deaths']

            latest = {
                'date': str(current_date),
                'total_cases': total_cases,
                'total_deaths': total_deaths,
                'new_cases': new_cases,
                'new_deaths': new_deaths
            }  

            return jsonify(latest)  

# API endpoints
api.add_resource(CountAll, "/api/<string:country>")
api.add_resource(CountLatest, "/api/<string:country>/latest")

# Website endpoints and handlers
@app.route('/')
def index():
    data = case_schema.dump(CaseModel.query.order_by(CaseModel.date).all())
    data_seven = data[-7:]
    total_cases_seven = data_seven[-1]['confirmed'] - data_seven[0]['confirmed']
    total_deaths_seven = data_seven[-1]['deaths'] - data_seven[0]['deaths']
    dash_data = {
        'total_cases': data_seven[-1]['confirmed'],
        'total_deaths': data_seven[-1]['deaths'],
        'total_cases_seven': total_cases_seven,
        'total_deaths_seven': total_deaths_seven,
        'average_cases_seven': round(total_cases_seven / 7, 2),
        'average_deaths_seven': round(total_deaths_seven / 7, 2)
    }
    return render_template('index.html', data=data, dash=dash_data)

@app.route('/api')
def api():
    return render_template('api.html')

if __name__ == "__main__":
    app.run(debug=True) 