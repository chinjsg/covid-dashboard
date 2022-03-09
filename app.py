from flask import Flask, render_template, request, redirect, jsonify, abort, url_for
from flask_restful import Api, Resource
from datetime import datetime
import requests
import csv
import db

app = Flask(__name__)
api = Api(app)

url = "https://api.github.com/repos/CSSEGISandData/COVID-19/contents/csse_covid_19_data/csse_covid_19_daily_reports"
file_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/"

# Index of the Country_Region column in each of 6-8-12-14 column formats
country_index = {
    6: 1,
    8: 1,
    12: 3,
    14: 3
}

# target = {'US': {'Arizona': ['Maricopa', 'Pima'], 'Washington': ['King']}, 'Singapore': {}, 'Japan': {'Tokyo':[]}}

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
        if cols == 12:
            new_row = [datestr] + row + [None, None]
        else:
            new_row = [datestr] + row
        new_row.pop(5)
    else:
        new_row = [None] * 14
        # Arrange the columns to match latest 14-columns format
        new_row[0] = datestr
        new_row[3] = row[0]
        new_row[4] = row[1]
        new_row[7] = row[3]
        new_row[8] = row[4]
        new_row[9] = row[5]
        if cols == 8:
            new_row[5] = row[6]
            new_row[6] = row[7]
    for i in range(len(new_row)):
        if new_row[i] == '':
            new_row[i] = None
            
    return new_row

class GetCountry(Resource):
    def get(self, country):
        exists = db.check_country_exists(country)
        if not exists:
            print("API: " + country + " does not exist")
            abort(404, description="Resource not found")
        else:
            data = db.get_latest_summary(country)
            return jsonify(data)  

class GetCountryPS(Resource):
    def get(self, country, province_state):
        exists = db.check_country_exists(country, province_state)
        if not exists:
            print("API: " + country + " or " + province_state + " does not exist")
            abort(404, description="Resource not found")
        else:
            data = db.get_latest_summary(country, province_state)
            return jsonify(data) 

class GetCountryPSCounty(Resource):
    def get(self, country, province_state, county):
        exists = db.check_country_exists(country, province_state, county)
        if not exists:
            print("API: " + country + ", " + province_state + ", or " + county + " does not exist")
            abort(404, description="Resource not found")
        else:
            data = db.get_latest_summary(country, province_state, county)
            return jsonify(data) 


class GetCountryAll(Resource):
    def get(self, country):
        exists = db.check_country_exists(country)
        if not exists:
            print("API: " + country + " does not exist")
            abort(404, description="Resource not found")
        else:
            data = db.get_cases(country)
            return jsonify(data)  

class GetCountryPSAll(Resource):
    def get(self, country, province_state):
        exists = db.check_country_exists(country, province_state)
        if not exists:
            print("API: " + country + " or " + province_state + " does not exist")
            abort(404, description="Resource not found")
        else:
            data = db.get_cases(country, province_state)
            return jsonify(data) 

class GetCountryPSCountyAll(Resource):
    def get(self, country, province_state, county):
        exists = db.check_country_exists(country, province_state, county)
        if not exists:
            print("API: " + country + ", " + province_state + ", or " + county + " does not exist")
            abort(404, description="Resource not found")
        else:
            data = db.get_cases(country, province_state, county)
            return jsonify(data) 

# API endpoints
api.add_resource(GetCountry, "/api/<string:country>/latest")
api.add_resource(GetCountryPS, "/api/<string:country>/<string:province_state>/latest")
api.add_resource(GetCountryPSCounty, "/api/<string:country>/<string:province_state>/<string:county>/latest")

api.add_resource(GetCountryAll, "/api/<string:country>")
api.add_resource(GetCountryPSAll, "/api/<string:country>/<string:province_state>")
api.add_resource(GetCountryPSCountyAll, "/api/<string:country>/<string:province_state>/<string:county>")

class GetListCountry(Resource):
    def get(self):
        data = db.get_countries()
        return jsonify(data)

class GetListProvinceState(Resource):
    def get(self, country):
        data = db.get_provinceState_by_country(country)
        return jsonify(data)

class GetListCounty(Resource):
    def get(self, country, province_state):
        data = db.get_county_by_countryState(country, province_state)
        return jsonify(data)

class GetAllByState(Resource):
    def get(self, country, province_state, county):
        data = db.get_cases(country, province_state, county)
        return jsonify(data)

# Webpage script endpoints
api.add_resource(GetListCountry, "/country")
api.add_resource(GetListProvinceState, "/country/<string:country>")
api.add_resource(GetListCounty, "/country/<string:country>/<string:province_state>")

api.add_resource(GetAllByState, "/all/<string:country>/<string:province_state>/<string:county>")

# Webpage endpoints and handlers
@app.route('/', methods=['GET', 'POST'])
def index():
    country_list = db.get_countries()['countries']
    # if 'US' in country_list:
    #     selection = ['US'] # default
    # else:
    selection = [country_list[0]]

    selected = request.args.get('selected')
    if selected is not None:
        selection = selected.split(',')
        count = len(selection)
        if count == 1:
            data = db.get_cases(selection[0])
            dash_data = db.get_latest_summary(selection[0])
        elif count == 2:
            data = db.get_cases(selection[0], selection[1])
            dash_data = db.get_latest_summary(selection[0], selection[1])
        else:
            data = db.get_cases(selection[0], selection[1], selection[2])
            dash_data = db.get_latest_summary(selection[0], selection[1], selection[2])
    else:
        print('Showing default')
        data = db.get_cases(selection[0])
        dash_data = db.get_latest_summary(selection[0])

    date_string = datetime.strptime(db.get_latest_date(selection[0]), "%Y-%m-%d").strftime("%B %e, %G")

    count = len(selection)
    
    ddl = []
    if count == 1:
        selected_country = selection[0]

        ddl_country = {
            'selected': selected_country,
            'options': country_list
        }
        ddl.append(ddl_country)
        prov_state_list = db.get_provinceState_by_country(selected_country)
        if prov_state_list['count'] > 0:
            ddl_provstate = {
                'selected': "",
                'options': prov_state_list['province_states']
            }
            ddl.append(ddl_provstate)

    elif count == 2:
        selected_country = selection[0]

        selected_provstate = selection[1]
        prov_state_list = db.get_provinceState_by_country(selected_country)

        ddl_country = {
            'selected': selected_country,
            'options': country_list
        }
        ddl_provstate = {
            'selected': selected_provstate,
            'options': prov_state_list['province_states']
        }
        ddl.append(ddl_country)
        ddl.append(ddl_provstate)

        county_list = db.get_county_by_countryState(selected_country, selected_provstate)
        if county_list['count'] > 0:
            ddl_county = {
                'selected': "",
                'options': county_list['counties']
            }
            ddl.append(ddl_county)
    else:
        selected_country = selection[0]

        selected_provstate = selection[1]
        prov_state_list = db.get_provinceState_by_country(selected_country)

        selected_county = selection[2]
        county_list = db.get_county_by_countryState(selected_country, selected_provstate)

        ddl_country = {
            'selected': selected_country,
            'options': country_list
        }
        ddl_provstate = {
            'selected': selected_provstate,
            'options': prov_state_list['province_states']
        }
        ddl_county = {
            'selected': selected_county,
            'options': county_list['counties']
        }
        ddl.append(ddl_country)
        ddl.append(ddl_provstate)
        ddl.append(ddl_county)

    location = ''
    for obj in reversed(ddl):
        if obj['selected'] != '':
            if location != '':
                location += ', '
            location += obj['selected']

    # Format of options
    # [ 
    #   {'selected': xxx, 'options'[]}, 
    #   {'selected': xxx, 'options'[]}, 
    #   {'selected': xxx, 'options'[]}
    # ]

    return render_template('index.html', data=data, dash=dash_data, ddl=ddl, loc=location, date=date_string)

@app.route('/api')
def api():
    return render_template('api.html', base_url=request.base_url)

@app.route('/update')
def update():
    # To remember selections in the dropdown lists
    country = request.args.get('country')
    province_state = request.args.get('province_state')
    county = request.args.get('county')

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

    last_date_str = datetime.strptime(db.get_latest_date(country), '%Y-%m-%d').strftime('%m-%d-%Y') + '.csv'
    index = filenames.index(last_date_str)
    filenames = filenames[index+1:]

    if len(filenames) == 0:
        print("Already up to date")
    else:
        print("New record found. Updating...")
        # For each file
        for fname in filenames:
            print('<Reading: ' + fname + '>')
            furl = file_url + fname

            response = requests.get(furl, timeout=5)
            response_decoded = [line.decode('utf-8') for line in response.iter_lines()]
            contents = list(csv.reader(response_decoded))
            
            # Check column names are at a maximum of 14 columns
            col_names = contents[0]
            #print(col_names)
            if (len(col_names) > 14 or len(col_names) < 14):
                print('Mismatched format. The number of columns is not 14. Exiting...')
                break

            # Read/Write each row to the database
            for row in contents[1:]:
                # These two lines skip "additional" empty rows that appear when iterating through certain csv files. Does not affect data.
                if len(row) == 0 or row == None:
                    continue
                
                datestr = datetime.strptime(fname.split('.')[0], "%m-%d-%Y").strftime("%Y-%m-%d")
                index = country_index[len(row)]
                retrieved_country = row[index]
                if retrieved_country == country:
                    row = update_format(row, len(col_names), datestr)
                    db.insert_case(retrieved_country, row)
                # isTarget = False
                # # get the index of the country_region column
                # index = country_index[len(row)]
                # country = row[index]
                # if country in target.keys():
                #     if len(target[country]) == 0:
                #         # For countries with no Province_state
                #         isTarget = True
                #     else:
                #         province_state = row[index-1]
                #         if province_state in target[country].keys():
                #             if country == "US":
                #                 # County name
                #                 county =  row[index-2]
                #                 if county in target[country][province_state]:
                #                     isTarget = True
                #             else:
                #                 isTarget = True

                # if isTarget:
                #     print(fname + ' - ' + country)
                #     case_date = datetime.strptime(fname.split('.')[0], '%m-%d-%Y').date()
                #     new_row = [case_date]
                #     for col in row:
                #         if col == '':
                #             new_row.append(None)
                #         else:
                #             new_row.append(col)
                #     # remove the last_updated column
                #     new_row.pop(col_names.index('Last_Update')+1)
                #     print(new_row)
                #     db.insert_case(new_row)


    selected = country
    if (province_state is not None and county is not None):
        selected += ',' + province_state + ',' + county
    elif (province_state is not None):
        selected += ',' + province_state
    
    return redirect(url_for('index', selected=selected))


if __name__ == "__main__":
    app.run(debug=True)