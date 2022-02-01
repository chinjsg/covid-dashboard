// To be moved server-side
// Calculate new cases from data
data[0]['newCases'] = data[0]['confirmed']
for (let i = 1; i < data.length; i++) {
    data[i]['newCases'] = data[i]['confirmed'] - data[i-1]['confirmed']
}

//////////////////////////////////////////////////////////////////////////////

let xScale = null;
let yScale = null;
let colorScale = null;

let xAxis = null;
let yAxis = null;

// Dimensions
let w = document.getElementById("daily-graph").parentNode.clientWidth;
let h = document.getElementById("daily-graph").parentNode.parentElement.offsetHeight;

let margin = {top: 5, right:10, bottom: 5, left: 45};
let width = w - margin.left - margin.right;
let height = h - margin.top - margin.bottom;

let svg = d3.select("#daily-graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);


let maxCase = d3.max(data, d => d.newCases);
let domainUpper = maxCase - (maxCase % 2500) + 2500;    // To be dynamic

// Create scales
xScale = d3.scaleBand()
    .domain(data.map(function(d) { return d.id; }))
    .range([0+margin.left, width-margin.right])

yScale = d3.scaleLinear()
    .domain([0, domainUpper])
    .range([height-margin.bottom, 0+margin.top])

// Axis object
yAxisGrid = d3.axisLeft(yScale)
    .ticks(domainUpper/2500)
    .tickValues(d3.range(0, domainUpper + 2500, 2500))
    .tickSize(-width)
    //.tickFormat(d3.format('d'))

// Create axis
svg.append("g")			
    .attr("class", "axis")
    .attr("transform", "translate("+ margin.left +", 0)")
    .call(yAxisGrid)

// Plot barcharts
svg.selectAll("rect")
    .data(data)
    .enter()
    .append("rect")
    .attr("x", function(d) { return xScale(d.id); })
    .attr("y", function(d) { return yScale(d.newCases); })
    .attr("width", 3)
    .attr("height", function(d) { return height-margin.bottom - yScale(d.newCases) })
    .attr("fill", "#ccc")