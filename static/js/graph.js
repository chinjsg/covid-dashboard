let xScale = null;
let yScale = null;
let colorScale = null;

let xAxis = null;
let yAxis = null;

let svg = null;

let margin = {top: 5, right:10, bottom: 5, left: 45};
let width = null;
let height = null;


createAll()

function createAll() {
    calculateNew()

    let maxCase = d3.max(cases, d => d.newCases);
    let domainUpper = detUpperDomain(maxCase)
    let interval = detInterval(domainUpper);

    getDimensions();
    createSvg();
    createScales(domainUpper)
    createAxis(domainUpper, interval)
    plotDailyNewCases()
}

function detInterval(domainUpper) {
    let zeroes = domainUpper.toString().length
    if ((domainUpper / 4).toString().length == zeroes) {
        return domainUpper / 4;
    } else {
        return domainUpper / 5;
    }
}

function detUpperDomain(maxCase) {
    if (maxCase < 10) {
        return 15;
    }
    let val = 10**(maxCase.toString().length - 1);
    let maxVal = Math.ceil(maxCase/val) * val;
    return maxVal;
}

function calculateNew() {
    cases[0]['newCases'] = cases[0]['confirmed']
    for (let i = 1; i < cases.length; i++) {
        let diff = cases[i]['confirmed'] - cases[i-1]['confirmed']
        if (diff < 0) {
            diff = 0
        }
        cases[i]['newCases'] = diff
    }
    //console.log(cases.length)
}

function getDimensions() {
    let w = document.getElementById("grid-graph").offsetWidth;
    let h = document.getElementById("grid-graph").offsetHeight;

    width = w - margin.left - margin.right;
    height = h - margin.top - margin.bottom;
}

function createSvg() {
    svg = d3.select("#daily-graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
}

function createScales(domainUpper) {
    // Create scales
    xScale = d3.scaleBand()
    .domain(cases.map(function(d) { return d.id; }))
    .range([0+margin.left, width-margin.right])

    yScale = d3.scaleLinear()
    .domain([domainUpper, 0])
    .range([0+margin.top, height-margin.bottom])
}

function createAxis(domainUpper, interval) {
    // Axis object
    yAxisGrid = d3.axisLeft(yScale)
    .ticks(domainUpper/interval)
    .tickValues(d3.range(0, domainUpper + interval, interval))
    .tickSize(-width)

    // Create axis
    svg.append("g")			
    .attr("class", "axis")
    .attr("transform", "translate("+ margin.left +", 0)")
    .call(yAxisGrid)
}

function plotDailyNewCases() {
    // Plot barcharts
    svg.selectAll("rect")
    .data(cases)
    .enter()
    .append("rect")
    .attr("x", function(d) { return xScale(d.id); })
    .attr("y", function(d) { return yScale(d.newCases); })
    .attr("width", 3)
    .attr("height", function(d) { return height-margin.bottom - yScale(d.newCases) })
    .attr("fill", "#ccc")
}

function updateSvg() {
    svg.remove();
    createAll();
}