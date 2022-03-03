import psycopg2
import psycopg2.extras
import config
import sys

#POSTGRESQL DATABASE
# Note: On Heroku, the free plan only has up to 10,000 rows


def get_conn():
    try:
        conn = psycopg2.connect(
                host = "localhost",
                database = config.db,
                user = config.user,
                password = config.password)

    except psycopg2.OperationalError as err:
        print(err)
        conn = None
    
    return conn

def get_cases(*arg):
    arg_count = len(arg)

    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if arg_count == 1:
        #stmt = "SELECT * FROM cases WHERE country_region=%s"
        stmt = "SELECT ROW_NUMBER() OVER (ORDER BY date) as id, date, SUM(confirmed) as confirmed FROM cases WHERE country_region=%s GROUP BY date ORDER BY date asc;"
    elif arg_count == 2:
        #stmt = "SELECT * FROM cases WHERE country_region=%s AND province_state=%s"
        stmt = "SELECT ROW_NUMBER() OVER (ORDER BY date) as id, date, SUM(confirmed) as confirmed FROM cases WHERE country_region=%s AND province_state=%s GROUP BY date ORDER BY date asc"
    else:
        stmt = "SELECT ROW_NUMBER() OVER (ORDER BY date) as id, date, confirmed FROM cases WHERE country_region=%s AND province_state=%s AND admin2=%s"
        arg = (arg[0], arg[1], arg[2])
    cursor.execute(stmt, arg)
    data = []
    for row in cursor.fetchall():
        data.append(dict(row))
    cursor.close()
    conn.close()
    return data

def get_latest_date():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM cases ORDER BY date DESC LIMIT 1")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data[0][0]

def get_combined_keys():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT combined_key FROM cases WHERE combined_key is not NULL")
    data = []
    for row in cursor.fetchall():
        data.append(row[0])
    cursor.close()
    conn.close()

    return data

def get_latest_summary(*arg):
    arg_count = len(arg)
    if arg_count == 1:
        #stmt = "SELECT * FROM cases WHERE LOWER(country_region) LIKE LOWER(%s) ORDER BY date DESC LIMIT 7"
        stmt = "SELECT date, SUM(confirmed) as confirmed, SUM(deaths) as deaths FROM cases WHERE LOWER(country_region) LIKE LOWER(%s) GROUP BY date ORDER BY date DESC LIMIT 7"
    elif arg_count == 2:
        #stmt = "SELECT * FROM cases WHERE LOWER(country_region) LIKE LOWER(%s) AND LOWER(province_state) LIKE LOWER(%s) ORDER BY date DESC LIMIT 7"
        stmt = "SELECT date, SUM(confirmed) as confirmed, SUM(deaths) as deaths FROM cases WHERE LOWER(country_region) LIKE LOWER(%s) AND LOWER(province_state) LIKE LOWER(%s) GROUP BY date ORDER BY date DESC LIMIT 7"
    else:
        stmt = "SELECT date, confirmed, deaths FROM cases WHERE LOWER(country_region) LIKE LOWER(%s) AND LOWER(province_state) LIKE LOWER(%s) AND LOWER(admin2) LIKE LOWER(%s) ORDER BY date DESC LIMIT 7"
        arg = (arg[0], arg[1], arg[2])


    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(stmt, arg)
    count = cursor.rowcount
    data = cursor.fetchall()
    #print('LATEST SUMMARY =========================================')
    #print(data[0])
    summary = {
        'date': data[0]['date'].strftime("%Y-%m-%d"),
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
    #print(summary)
    return summary

def get_countries():
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT DISTINCT country_region FROM cases")
    data = cursor.fetchall()
    count = cursor.rowcount
    cursor.close()
    conn.close()

    results = {'countries': [], 'count': count}
    for d in data:
        results['countries'].append(d[0])

    return results

def get_provinceState_by_country(country):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT province_state FROM cases WHERE country_region=%s AND province_state IS NOT NULL" , (country,))
    data = cursor.fetchall()
    count = cursor.rowcount
    cursor.close()
    conn.close()

    results = {'province_states': [], 'count': count}
    for d in data:
        results['province_states'].append(d[0])

    return results

def get_county_by_countryState(country, province_state):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT admin2 FROM cases WHERE country_region=%s AND province_state=%s AND admin2 IS NOT NULL", (country, province_state))
    data = cursor.fetchall()
    count = cursor.rowcount
    cursor.close()
    conn.close()

    results = {'counties': [], 'count': count}
    for d in data:
        results['counties'].append(d[0])

    return results

def insert_case(params):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO ' +
                    'cases(date, fips, admin2, province_state, country_region, lat, long_, confirmed, deaths, recovered, active, combined_key, incidence_rate, case_fatality_ratio) ' +
                    'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ',
                    params)
    cursor.close()
    conn.commit()
    conn.close()

def check_country_exists(*arg):
    arg_count = len(arg)
    if arg_count == 1:
        stmt = "SELECT * FROM cases WHERE LOWER(country_region) LIKE LOWER(%s)"
    elif arg_count == 2:
        stmt = "SELECT * FROM cases WHERE LOWER(country_region) LIKE LOWER(%s) AND LOWER(province_state) LIKE LOWER(%s)"
    else:
        stmt = "SELECT * FROM cases WHERE LOWER(country_region) LIKE LOWER(%s) AND LOWER(province_state) LIKE LOWER(%s) AND LOWER(admin2) LIKE LOWER(%s)"
        arg = (arg[0], arg[1], arg[2])

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(stmt, arg)
    count = cursor.rowcount
    cursor.close()
    conn.close()
    return (count > 0)
