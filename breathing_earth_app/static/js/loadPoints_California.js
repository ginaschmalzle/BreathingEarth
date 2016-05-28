function initMap() {
    // Create the map.
    //TODO: Update Center Lat Lng to be more centralized to our data set
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 6,
        center: {
            lat: 36.016,
            lng: -118.370
        },
        mapTypeId: google.maps.MapTypeId.HYBRID
    });

    getCoordinates(function(response) {
        coordlist = JSON.parse(response);
    });

    load_california(function(response) {
        // Parse JSON string into object
        datelist = JSON.parse(response);

        for (var dates in datelist) {
            datelistArray.push(dates);
            datelistArray.sort();
        };
        getMinMaxDates();

        var date = datelistArray[1];
        console.log(date);
        parsePointsInDate(date);
        fillTableAndPlotPoints();
    });
}

function load_california(callback) {
    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.open('GET', 'static/data/positions_sample_size_30_sqlite_sw.json', true); // Replace 'my_data' with the path to your file
    xobj.onreadystatechange = function() {
        if (xobj.readyState == 4 && xobj.status == "200") {
            // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
            callback(xobj.responseText);
        }
    };
    xobj.send(null);
}
