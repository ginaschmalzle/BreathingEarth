var coordlist = {};
var datelist = {};
var datelistArray = [];

var minMonth = 0;
var maxMonth = 0;
var minYear = 0;
var maxYear = 0;

var currentLocPoint = [];
var pointsInDate = [];
var dateForPointsInDate = "";

var map;
var cityCircle;
var Circles = [];

//Set slider start/end
//TODO: dynamically set per data
$(function() {
        $("#slider").slider({
            value: 1,
            min: 0,
            max: 101,
            step: 1,
            slide: function(event, ui) {
                $("#amount").val(ui.value);
            }
        });
        $("#amount").val('2008-01-31');
    });
$(function() {
    $("#slider").on("slidechange", function(event, ui) {
        var date = datelistArray[ui.value];
        var short_date = date.split(' ');
        short_date = short_date[0];
        $('#amount').val(short_date);
        parsePointsInDate(date);
        fillTableAndPlotPoints();
        updateTable();
    });
});

//Grab all the points that had changes for the date and store in pointsInDate object
function parsePointsInDate(dateval) {
    dateForPointsInDate = dateval;
    pointsInDate = [];
    pointsInDate = Object.keys(datelist[dateval]);
}

//get the change to write to table (and later to adjust circle color)
function parseChangeInPointsByDate(dateval, pointName) {
    return datelist[dateval][pointName];
}

//Return the lat and lng for GPS Site
function getLngLatFromSiteName(pointName) {
    return 'lat: '+coordlist[pointName].lat + ' | lng: '+coordlist[pointName].lng;
}

//Remove all points from map and table
function garbageCollectMapPoints() {
    for(var x = 0; x < Circles.length; x++) {
      Circles[x].setMap(null);
    }
    Circles = [];
}

function updateTable(pointName, changedValue) {
    if($('#'+pointName+'_change').length > 0)
        $('#'+ pointName +'_change').text(parseFloat(changedValue).toFixed(4));

}

function plotPoints(pointName) {
    var changedValue = parseChangeInPointsByDate(dateForPointsInDate,pointName)*1000000;
    var color = (changedValue > 0) ? '#FF0000' : '#0000FF';

    cityCircle = {
        strokeColor: color,
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: color,
        fillOpacity: 0.35,
        map: map,
        center: coordlist[pointName], //.coordinates,
        radius: changedValue, //Math.sqrt(citymap[city].adj_du) * 100000
        clickable: true,
        name: pointName
    };
    updateTable(pointName, (changedValue/1000000));
    google.maps.event.addListener(cityCircle, 'click', function(ev){
        $('#datatable').append("<tr><td>"+pointName+"</td><td>"+coordlist[pointName].lat+"</td><td>"+coordlist[pointName].lng+"</td><td id='"+pointName+"_change'>"+parseFloat(parseChangeInPointsByDate(dateForPointsInDate,pointName)).toFixed(4)+"</td></tr>");
    });
    Circles.push(new google.maps.Circle(cityCircle));
}

function fillTableAndPlotPoints() {
    //Clear existing data
    garbageCollectMapPoints();
    //loop through new data points and plot on map
    for(var x = 0; x < pointsInDate.length; x++)
    {
      plotPoints(pointsInDate[x]);
    }
}

//TODO: Could replace with jQuery if we decide to use, dont have to
function getCoordinates(callback) {
    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.open('GET', 'static/data/coordinates_sqlite.json', true); // Replace 'my_data' with the path to your file
    xobj.onreadystatechange = function() {
        if (xobj.readyState == 4 && xobj.status == "200") {
            // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
            callback(xobj.responseText);
        }
    };
    xobj.send(null);
}

//Get min/max dates for determining start/end points on slider
function getMinMaxDates() {
    minMonth = datelistArray[0].split('-')[1];
    minYear = datelistArray[0].split('-')[0];
    maxMonth = datelistArray[datelistArray.length-1].split('-')[1];
    maxYear = datelistArray[datelistArray.length-1].split('-')[0];
}
