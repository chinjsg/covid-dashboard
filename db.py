# import psycopg2
# import psycopg2.extras
from datetime import datetime
import sqlite3

#POSTGRESQL DATABASE
# Note: On Heroku, the free plan only has up to 10,000 rows

def formatStr(str): # or just use regex since we do not need to preserve
    str = str.strip()
    str = str.lower().replace(" ", "")
    str = str.replace(" ", "")
    str = str.replace(".", "") # e.g. st. martin
    str = str.replace(",", "") # e.g. Korea, South
    str = str.replace("(", "").replace(")", "") # e.g. Congo (Kinshasa) / Congo ()
    str = str.replace("'", "") # e.g. Cote d'Ivoire
    str = str.replace("-", "") # e.g. Timor-Leste
    return str

def makeDict(num_fields, field_names, rows):
    result = []
    for row in rows:
        dict = {}
        for i in range(num_fields):
            dict[field_names[i]] = row[i]
        result.append(dict)
    return result

def get_conn():
    # try:
    #     conn = psycopg2.connect(
    #             host = "localhost",
    #             database = config.db,
    #             user = config.user,
    #             password = config.password)

    # except psycopg2.OperationalError as err:
    #     print(err)
    #     conn = None
    conn = sqlite3.connect("cases_all.db")
    
    return conn

def get_cases(*arg):
    arg_count = len(arg)

    table_name = formatStr(arg[0])
    conn = get_conn()
    cursor = conn.cursor()
    if arg_count == 1:
        stmt = "SELECT ROW_NUMBER() OVER (ORDER BY date) as id, date, SUM(confirmed) as confirmed FROM {} WHERE country_region=? GROUP BY date ORDER BY date(date) ASC"
    elif arg_count == 2:
        stmt = "SELECT ROW_NUMBER() OVER (ORDER BY date) as id, date, SUM(confirmed) as confirmed FROM {} WHERE country_region=? AND province_state=? GROUP BY date ORDER BY date ASC    "
    else:
        stmt = "SELECT ROW_NUMBER() OVER (ORDER BY date) as id, date, confirmed FROM {} WHERE country_region=? AND province_state=? AND admin2=?"
        arg = (arg[0], arg[1], arg[2])
    cursor.execute(stmt.format(table_name), arg)
    num_fields = len(cursor.description)
    field_names = [i[0] for i in cursor.description]
    data = makeDict(num_fields, field_names, cursor.fetchall())
    cursor.close()
    conn.close()
    return data

def get_latest_date(country):
    table_name = formatStr(country)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM {} ORDER BY date DESC LIMIT 1".format(table_name))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data[0][0]

def get_latest_summary(*arg):
    arg_count = len(arg)
    table_name = formatStr(arg[0])
    if arg_count == 1:
        stmt = "SELECT date, SUM(confirmed) as confirmed, SUM(deaths) as deaths FROM {} WHERE LOWER(country_region) LIKE LOWER(?) GROUP BY date ORDER BY date DESC LIMIT 7"
    elif arg_count == 2:
        stmt = "SELECT date, SUM(confirmed) as confirmed, SUM(deaths) as deaths FROM {} WHERE LOWER(country_region) LIKE LOWER(?) AND LOWER(province_state) LIKE LOWER(?) GROUP BY date ORDER BY date DESC LIMIT 7"
    else:
        stmt = "SELECT date, confirmed, deaths FROM {} WHERE LOWER(country_region) LIKE LOWER(?) AND LOWER(province_state) LIKE LOWER(?) AND LOWER(admin2) LIKE LOWER(?) ORDER BY date DESC LIMIT 7"
        arg = (arg[0], arg[1], arg[2])

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(stmt.format(table_name), arg)
    #count = cursor.rowcount
    num_fields = len(cursor.description)
    field_names = [i[0] for i in cursor.description]
    results = cursor.fetchall()
    count = len(results)
    data = makeDict(num_fields, field_names, results)
    summary = {
        'date': data[0]['date'],
        'date_long': datetime.strptime(data[0]['date'], "%Y-%m-%d").strftime("%B %e, %G"),
        'total_cases': data[0]['confirmed'],
        'total_deaths': data[0]['deaths'],
        'new_cases': data[0]['confirmed'] - data[1]['confirmed'],
        'new_deaths': data[0]['deaths'] - data[1]['deaths'],
        'total_cases_7': data[0]['confirmed'] - data[-1]['confirmed'],
        'total_deaths_7': data[0]['deaths'] - data[-1]['deaths'],
        'average_cases_7': round((data[0]['confirmed'] - data[-1]['confirmed']) / count, 2) ,
        'average_deaths_7': round((data[0]['deaths'] - data[-1]['deaths']) / count, 2)
    }
    cursor.close()
    conn.close()
    return summary

def get_countries():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM country ORDER BY name ASC")
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    results = {'countries': []}
    for d in data:
        results['countries'].append(d[0])
    results['count'] = len(results['countries'])

    return results

def get_provinceState_by_country(country):
    table_name = formatStr(country)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT province_state FROM {} WHERE country_region=? AND province_state IS NOT NULL ORDER BY province_state ASC".format(table_name) , (country,))
    data = cursor.fetchall()
    #count = cursor.rowcount
    cursor.close()
    conn.close()

    results = {'province_states': []}
    for d in data:
        results['province_states'].append(d[0])
    results['count'] = len(results['province_states'])

    return results

def get_county_by_countryState(country, province_state):
    table_name = formatStr(country)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT admin2 FROM {} WHERE country_region=? AND province_state=? AND admin2 IS NOT NULL ORDER BY admin2 ASC".format(table_name), (country, province_state))
    data = cursor.fetchall()
    #count = cursor.rowcount
    cursor.close()
    conn.close()

    results = {'counties': []}
    for d in data:
        results['counties'].append(d[0])
    results['count'] = len(results['counties'])

    return results

def insert_case(table_name, params):
    table_name = formatStr(table_name)
    conn = get_conn()
    cursor = conn.cursor()
    stmt = 'INSERT INTO {}'.format(table_name)
    stmt += '''(date, fips, admin2, province_state, country_region, lat, long_, confirmed, deaths, recovered, active, combined_key, incidence_rate, case_fatality_ratio) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    cursor.execute(stmt, params)
    cursor.close()
    conn.commit()
    conn.close()

def check_country_exists(*arg):
    arg_count = len(arg)
    table_name = formatStr(arg[0])
    if arg_count == 1:
        stmt = "SELECT * FROM {} WHERE LOWER(country_region) LIKE LOWER(?)".format(table_name)
    elif arg_count == 2:
        stmt = "SELECT * FROM {} WHERE LOWER(country_region) LIKE LOWER(?) AND LOWER(province_state) LIKE LOWER(?)".format(table_name)
    else:
        stmt = "SELECT * FROM {} WHERE LOWER(country_region) LIKE LOWER(?) AND LOWER(province_state) LIKE LOWER(?) AND LOWER(admin2) LIKE LOWER(?)".format(table_name)
        arg = (arg[0], arg[1], arg[2])

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(stmt, arg)
    count = len(cursor.fetchall())
    cursor.close()
    conn.close()
    return (count > 0)
