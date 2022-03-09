
let selCountry = document.getElementById('country');
let selProvState = document.getElementById('province_state');
let selCounty = document.getElementById('county');

// Elements
let lblCountryName = document.getElementById('country-name');
let lblCaseDate = document.getElementById('case-date');

let totalCases = document.getElementById('total-cases');
let totalCasesNew = document.getElementById('total-cases-new');
let totalCasesSeven = document.getElementById('total-cases-seven');
let totalCasesSevenAvg = document.getElementById('total-cases-seven-avg');

let totalDeaths = document.getElementById('total-deaths');
let totalDeathsNew = document.getElementById('total-deaths-new');
let totalDeathsSeven = document.getElementById('total-deaths-seven');
let totalDeathsSevenAvg = document.getElementById('total-deaths-seven-avg');

document.getElementById('update').onclick = function addParams() {
    country = selCountry.value
    province_state = selProvState.value
    county = selCounty.value
    params = "?country=" + country
    if (province_state !== "" && county !== "") {
        params += "&province_state=" + province_state + "&county=" + county
    } else if (province_state !== "") {
        params += "&province_state=" + province_state
    }
    this.setAttribute('href', '/update' + params);
}


// Call func to update graph
window.onresize = updateSvg;

selCountry.onchange = function() {
    let country = selCountry.value
    if (country !== "") {
        fetch('/country/' + country).then(function(response) {
            response.json().then(function(selectOptions) {
                updateDropdown(selectOptions)
                fetch('/api/' + country + "/latest").then(function(response) {
                    response.json().then(function(data) {
                        let location = country
                        updateDashboard(data, location, country, "", "");
                    });
                });
            });
        });
    }
}

selProvState.onchange = function() {
    let country = selCountry.value
    let province_states = selProvState.value
    if (province_states !== "") {
        fetch('/country/' + country + '/' + province_states).then(function(response) {
            response.json().then(function(selectOptions) {
                updateDropdown(selectOptions)
                fetch('/api/' + country + '/' + province_states + "/latest").then(function(response) {
                    response.json().then(function(data) {
                        let location = province_states + ', ' + country
                        updateDashboard(data, location, country, province_states, "");
                    });
                });
            });
        });
    } else {
        fetch('/api/' + country + "/latest").then(function(response) {
            response.json().then(function(data) {
                let location = country
                updateDashboard(data, location, country, province_states, "");
            });
        });
        if (!selCounty.disabled) {
            selCounty.disabled = true;
            selCounty.innerHTML = '<option value="">-</option>';
        }
    }
}

selCounty.onchange = function() {
    let country = selCountry.value
    let province_states = selProvState.value
    let county = selCounty.value
    if (county !== "") {
        fetch('/api/' + country + '/' + province_states + '/' + county + "/latest").then(function(response) {
            response.json().then(function(data) {
                let location = county + ', ' + province_states + ', ' + country
                updateDashboard(data, location, country, province_states, county);
            });
        });
    } else {
        fetch('/api/' + country + '/' + province_states + "/latest").then(function(response) {
            response.json().then(function(data) {
                let location = province_states + ', ' + country
                updateDashboard(data, location, country, province_states, county);
            });
        });
    }
}

function updateDropdown(options) {
    if (options.hasOwnProperty('province_states')) {
        if (options.count > 0) {
            selProvState.disabled = false;
            selCounty.disabled = true;
            selProvState.innerHTML = '<option value="">- Province/State -</option>';
            for (item of options.province_states) {
                selProvState.innerHTML += '<option value="'+item+'">'+item+'</option>';
            }
            selCounty.innerHTML = '<option value="">-</option>';
        } else {
            selProvState.disabled = true;
            selCounty.disabled = true;
            selProvState.innerHTML = '<option value="">-</option>';
            selCounty.innerHTML = '<option value="">-</option>';
        }
    } else if (options.hasOwnProperty('counties')){
        if (options.count > 0) {
            selCounty.disabled = false;
            selCounty.innerHTML = '<option value="">- County -</option>';
            for (item of options.counties) {
                selCounty.innerHTML += '<option value="'+item+'">'+item+'</option>';
            }
        } else {
            selCounty.disabled = true;
            selCounty.innerHTML = '<option value="">-</option>';
        }
    }
}

function updateDashboard(data, loc, country, province_state, county) {
    lblCountryName.innerHTML = 'Cases in ' + loc;
    lblCaseDate.innerHTML = data.date_long;

    totalCases.innerHTML = data.total_cases;
    totalCasesNew.innerHTML = data.new_cases;
    totalCasesSeven.innerHTML = data.total_cases_7
    totalCasesSevenAvg.innerHTML = data.average_cases_7

    totalDeaths.innerHTML = data.total_deaths
    totalDeathsNew.innerHTML = data.new_deaths
    totalDeathsSeven.innerHTML = data.total_deaths_7
    totalDeathsSevenAvg.innerHTML = data.average_deaths_7

    if (data.new_cases == 0) {
        totalCasesNew.innerHTML = '-'
    } else {
        totalCasesNew.innerHTML = '+' + data.new_cases
    }
    if (data.new_deaths == 0) {
        totalDeathsNew.innerHTML = '-'
    } else {
        totalDeathsNew.innerHTML = '+' + data.new_deaths
    }

    // Get all cases
    url = "/api/" + country
    if (province_state !== "" && county !== "") {
        url += "/" + province_state + "/" + county
    } else if (province_state !== "") {
        url += "/" + province_state
    }

    fetch(url).then(function(response) {
        response.json().then(function(data) {
            cases = data
            updateSvg()
        });
    });
}