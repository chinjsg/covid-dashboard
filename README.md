# COVID-19 Dashboard

COVID-19 Dashboard is a personal project that is designed to visualize COVID-19 data of locations throughout the world at a glance. The data source comes from the public JHU CSSE Github repository and is processed to produce numbers, such as new cases, new deaths, and produces a graph on these numbers for easy visualization. As this project is ongoing development, it currently supports two locations and will gradually expand to support more in the future.  
  
If you are interested, the web application can be viewed at https://covid-case-dashboard.herokuapp.com/
This version displays data from Singapore and US (Pima, Arizona) only.
As Heroku uses an ephemeral filesystem, the data will be reset periodically and has to be manually updated via the button in the web application. There are plans to resolve this by changing the implemented database.


## References
* JHU Coronavirus Resource Center (https://coronavirus.jhu.edu/)
* JHU CSSE COVID-19 Dataset (https://github.com/CSSEGISandData/COVID-19)
* GitHub REST API (https://docs.github.com/en/rest)