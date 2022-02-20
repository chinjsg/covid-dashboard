from flask import Flask, render_template, request, redirect, json, jsonify, abort
from flask_restful import Api, Resource
from datetime import date, datetime
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

class CountLatest(Resource):
    def get(self, country):
        exists = db.check_country_exists(country)
        if not exists:
            print("API: " + country + " does not exist")
            abort(404, description="Resource not found")
        else:
            data = db.get_latest_summary(country)
            return jsonify(data)  

# API endpoints
api.add_resource(CountLatest, "/api/<string:country>/latest")

# Website endpoints and handlers
@app.route('/', methods=['GET', 'POST'])
def index():
    selection = "Pima, Arizona, US"
    options = db.get_combined_keys()


    if request.method == 'POST':
        selection = request.form['selection']
        sel = selection.replace(" ", "").split(',')
        # Example format ['Pima', 'Arizona', 'US']
        count = len(sel)
        if count == 1:
            data = db.get_cases(sel[0])
        elif count == 2:
            data = db.get_cases(sel[1], sel[0])
        else:
            data = db.get_cases(sel[2], sel[1], sel[0])
    else:
        data = db.get_cases('US', 'Arizona', 'Pima')


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

    date_string = data[-1]['date'].strftime("%B %e, %G")

    if selection == "":
        selection = options.pop()
    else:
        options.remove(selection)
    options = [selection, options]

    return render_template('index.html', data=data, dash=dash_data, options=options, date=date_string)

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

    current_date = db.get_latest_date()
    current_date = current_date.strftime('%m-%d-%Y')

    last_date_str = current_date + '.csv'
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

                isTarget = False
                # get the index of the country_region column
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
                    print(fname + ' - ' + country)
                    case_date = datetime.strptime(fname.split('.')[0], '%m-%d-%Y').date()
                    new_row = [case_date]
                    for col in row:
                        if col == '':
                            new_row.append(None)
                        else:
                            new_row.append(col)
                    # remove the last_updated column
                    new_row.pop(col_names.index('Last_Update')+1)
                    db.insert_case(new_row)

    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True) 





