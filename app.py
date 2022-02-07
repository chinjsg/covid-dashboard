from flask import Flask, render_template, request, redirect, json, jsonify, abort
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from flask_marshmallow import Marshmallow
import requests
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cases.db'
db = SQLAlchemy(app)
api = Api(app)
ma = Marshmallow(app)

url = "https://api.github.com/repos/CSSEGISandData/COVID-19/contents/csse_covid_19_data/csse_covid_19_daily_reports"
file_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/"

# Index of the Country_Region column in each of 6-8-12-14 column formats
country_index = {
    6: 1,
    8: 1,
    12: 3,
    14: 3
}

target = {'US': {'Arizona': ['Pima']}, 'Singapore': {}}

def format_datestr(datestr):
    """
    Format a date string to match mm-dd-YYYY and fill in leading zeroes
    """
    if '/' in datestr:
        datestr = datestr.split('/')
    elif '-' in datestr:
        datestr = datestr.split('-')
    datestr[0] = datestr[0].zfill(2)
    datestr[1] = datestr[1].zfill(2)

    return '-'.join(datestr)

def update_format(row, cols, datestr):
    """
    Handle two early formats that vary significantly.
    This method simply swaps the columns around to match the current format

    Note: There are a total of 4 different formats gathered from all csv files. 
    Each format has 6, 8, 12, 14 columns respectively, where 6 and 8 is out of order, while 12 differs by an addition of two columns at the end, and 14 being the one we want to match.
    """
    if cols >= 12:
        new_row = [datestr] + row
    else:
        new_row = [None] * 15

        # Arrange the columns to match latest 14-columns format
        new_row[0] = datestr
        new_row[2] = row[0]
        new_row[4] = row[1]
        new_row[5] = row[2]
        new_row[8] = row[3]
        new_row[9] = row[4]
        new_row[10] = row[5]
        if cols == 8:
            new_row[6] = row[6]
            new_row[7] = row[7]

    return new_row

class CaseModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    fips = db.Column(db.String(100))
    admin2 = db.Column(db.String(100))
    province_state = db.Column(db.String(100))
    country_region = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Float)
    long_ = db.Column(db.Float)
    confirmed = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    recovered = db.Column(db.Integer)
    active = db.Column(db.Integer)
    combined_key = db.Column(db.String(200))
    incidence_rate = db.Column(db.Float)
    case_fatality_ratio = db.Column(db.Float)

    def __repr__(self):
        return "<CaseModel {'id':%s, 'date':%s, 'country_region':%s, 'confirmed':%s, 'deaths':%s}>" % (self.id, self.date, self.country_region, self.confirmed, self.deaths)

# Multiple Day Case Schema
class CaseSchema(ma.Schema):
  class Meta:
    fields = ('id', 'date', 'country_region', 'confirmed', 'deaths', 'combined_key')

# Single Day Case Schema
class DailySchema(ma.Schema):
  class Meta:
    fields = ('date', 'confirmed', 'deaths', 'recovered', 'active')

# Init schema
daily_schema = DailySchema()
case_schema = CaseSchema(many=True)

#

# API endpoint handlers
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
@app.route('/', methods=['GET', 'POST'])
def index():
    selection = "Pima, Arizona, US"
    options = []
    for ck in db.session.query(CaseModel.combined_key).distinct():
        ck = str(ck)
        ck = ck.replace("(", "").replace(")", "").replace("'", "").rstrip(',')
        if ck != "":
            options.append(ck)

    if request.method == 'POST':
        selection = request.form['selection']
        sel = selection.replace(" ", "").split(',')
        count = len(sel)
        if count == 1:
            data = case_schema.dump(CaseModel.query.filter_by(country_region=sel[0]).order_by(CaseModel.date).all())
        elif count == 2:
            data = case_schema.dump(CaseModel.query.filter_by(country_region=sel[1], province_state=sel[0]).order_by(CaseModel.date).all())
        else:
            data = case_schema.dump(CaseModel.query.filter_by(country_region=sel[2], province_state=sel[1], admin2=sel[0]).order_by(CaseModel.date).all())
    else:
        data = case_schema.dump(CaseModel.query.filter_by(country_region='US', province_state='Arizona', admin2='Pima').order_by(CaseModel.date).all())

    data_seven = data[-7:]
    total_cases_seven = data_seven[-1]['confirmed'] - data_seven[0]['confirmed']
    total_deaths_seven = data_seven[-1]['deaths'] - data_seven[0]['deaths']
    new_cases = data_seven[-1]['confirmed'] - data_seven[-2]['confirmed']
    new_deaths = data_seven[-1]['deaths'] - data_seven[-2]['deaths']
    dash_data = {
        'total_cases': data_seven[-1]['confirmed'],
        'total_deaths': data_seven[-1]['deaths'],
        'total_cases_seven': total_cases_seven,
        'total_deaths_seven': total_deaths_seven,
        'average_cases_seven': round(total_cases_seven / 7, 2),
        'average_deaths_seven': round(total_deaths_seven / 7, 2),
        'new_cases': new_cases,
        'new_deaths': new_deaths
    }
    
    datestr = datetime.strptime(data[-1]['date'].split('T')[0], '%Y-%m-%d').strftime("%c")
    datestr= datestr.split(' ')
    datestr = datestr[1] + ' ' + datestr[3] + ', ' + datestr[5]

    if selection == "":
        selection = options.pop()
    else:
        options.remove(selection)
    options = [selection, options]

    return render_template('index.html', data=data, dash=dash_data, options=options, date=datestr)

@app.route('/api')
def api():
    return render_template('api.html')

@app.route('/update')
def update():
    '''Modified CSV extractor code'''
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.Timeout:
        # Timeout
        print('Connection timeout')
        return redirect('/')
    except requests.exceptions.TooManyRedirects:
        # Notify user of invalid URL
        print('Bad URL. Check URL and retry')
        return redirect('/')
    except requests.exceptions.RequestException as e:
        # Error
        print('An error occured')
        return redirect('/')

    directory = response.json()
    filenames = [] 
    for file in directory:
        if file['type'] == 'file' and file['name'].split('.')[1] == 'csv':
            filenames.append(file['name'])
    filenames.sort(key = lambda fname: datetime.strptime(fname.split('.')[:1][0], '%m-%d-%Y'))

    current = CaseModel.query.order_by(CaseModel.date.desc()).first()
    current = daily_schema.dump(current)
    current_date = str(datetime.strptime(current['date'].split('T')[0], '%Y-%m-%d').date().strftime('%m-%d-%Y'))

    last_date_str = current_date + '.csv'
    index = filenames.index(last_date_str)
    filenames = filenames[index+1:]

    if len(filenames) == 0:
        print("Already up to date")
    else:
        print("Updating...")
        # For each file
        for fname in filenames:
            print('<Adding: ' + fname + '>')
            furl = file_url + fname

            response = requests.get(furl, timeout=5)
            response_decoded = [line.decode('utf-8') for line in response.iter_lines()]
            contents = list(csv.reader(response_decoded))
            
            # Check columns are at a maximum of 14 columns
            col_names = contents[0]
            if (len(col_names) > 14):
                print('There are more than 14 columns and program needs to be updated. Exiting...')
                break

            # Read/Write each row to the database
            for row in contents[1:]:
                # These two lines skip "additional" empty rows that appear when iterating through certain csv files. Does not affect data.
                if len(row) == 0 or row == None:
                    continue

                isTarget = False
                index = country_index[len(row)]
                country = row[index]
                if country in target.keys():
                    if len(target[country]) == 0:
                        # For countries with no Province_state
                        isTarget = True
                    else:
                        province_state = row[index-1]
                        if province_state in target[country].keys():
                            if country == "US":
                                # County name
                                county =  row[index-2]
                                if county in target[country][province_state]:
                                    isTarget = True
                            else:
                                isTarget = True
            
                if isTarget:
                    print(row)
                    print(fname)
                    new_row = CaseModel(date=datetime.strptime(fname.split('.')[0], '%m-%d-%Y'),
                                        fips=row[0],
                                        admin2=row[1],
                                        province_state=row[2],
                                        country_region=row[3],
                                        #last_update=row[5],
                                        lat=row[5],
                                        long_=row[6],
                                        confirmed=row[7],
                                        deaths=row[8],
                                        recovered=row[9],
                                        active=row[10],
                                        combined_key=row[11],
                                        incidence_rate=row[12],
                                        case_fatality_ratio=row[13])
                    try:
                        db.session.add(new_row)
                        db.session.commit()
                    except:
                        print('There was a problem inserting into the database')

    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True) 





