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

    function initMap() {
        // Create the map.
        //TODO: Update Center Lat Lng to be more centralized to our data set
        map = new google.maps.Map(document.getElementById('map'), {
            zoom: 5,
            center: {
                lat: 45.090,
                lng: -120.712
            },
            mapTypeId: google.maps.MapTypeId.TERRAIN
        });


        getCoordinates(function(response) {
            coordlist = JSON.parse(response);
            //console.log(coordlist);

        });

        sortDateList(function(response) {
            // Parse JSON string into object
            datelist = JSON.parse(response);
            //console.log(datelist);

            for (var dates in datelist) {
                //console.log(dates);
                datelistArray.push(dates);
                datelistArray.sort();
            };
            getMinMaxDates();
        })
    }

    //Get min/max dates for determining start/end points on slider
    function getMinMaxDates() {
        minMonth = datelistArray[0].split('-')[1];
        minYear = datelistArray[0].split('-')[0];
        maxMonth = datelistArray[datelistArray.length-1].split('-')[1];
        maxYear = datelistArray[datelistArray.length-1].split('-')[0];

    }

    //Set slider start/end
    //TODO: dynamically set per data
    $(function() {
            $("#slider").slider({
                value: 0,
                min: 0,
                max: 101,
                step: 1,
                slide: function(event, ui) {
                    $("#amount").val(ui.value);
                }
            });
            $("#amount").val($("#slider").slider("value"));
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
        document.querySelector('#datatable').innerHTML = '<table id="datatable" class="text-center table table-striped"><thead><tr><th>Loc</th><th>Lat</th><th>Lng</th><th>Change</th></tr></thead></table>';
    }

    function plotPoints(pointName) {
        cityCircle = {
            strokeColor: '#FF0000',
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: '#FF0000',
            fillOpacity: 0.35,
            map: map,
            center: coordlist[pointName], //.coordinates,
            radius: 10000 //Math.sqrt(citymap[city].adj_du) * 100000
        };

        Circles.push(new google.maps.Circle(cityCircle));
    }

    function fillTable(pointName) {        
        $('#datatable').append("<tr><td>"+pointName+"</td><td>"+coordlist[pointName].lat+"</td><td>"+coordlist[pointName].lng+"</td><td>"+parseChangeInPointsByDate(dateForPointsInDate,pointName)+"</td></tr>");
    }

    function fillTableAndPlotPoints() {
        //Clear existing data
        garbageCollectMapPoints();

        //loop through new data points and plot on map
        for(var x = 0; x < pointsInDate.length; x++)
        {
          plotPoints(pointsInDate[x]);
          //TODO: Add table with pagination support (datatables?)
          if(x < 11) 
            fillTable(pointsInDate[x]);
        }
    }


    //TODO: Could replace with jQuery if we decide to use, dont have to
    function getCoordinates(callback) {
        var xobj = new XMLHttpRequest();
        xobj.overrideMimeType("application/json");
        xobj.open('GET', 'static/data/coordinates.json', true); // Replace 'my_data' with the path to your file
        xobj.onreadystatechange = function() {
            if (xobj.readyState == 4 && xobj.status == "200") {
                // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
                callback(xobj.responseText);
            }
        };
        xobj.send(null);
    }

    function sortDateList(callback) {
        var xobj = new XMLHttpRequest();
        xobj.overrideMimeType("application/json");
        xobj.open('GET', 'static/data/positions_sample_size_30_pnw.json', true); // Replace 'my_data' with the path to your file
        xobj.onreadystatechange = function() {
            if (xobj.readyState == 4 && xobj.status == "200") {
                // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
                callback(xobj.responseText);
            }
        };
        xobj.send(null);
    }