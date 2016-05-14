    var citymap = {};

    function initMap() {
        // Create the map.
        //TODO: Update Center Lat Lng to be more centralized to our data set
        var map = new google.maps.Map(document.getElementById('map'), {
            zoom: 5,
            center: {
                lat: 45.090,
                lng: -120.712
            },
            mapTypeId: google.maps.MapTypeId.TERRAIN
        });

         loadJSON(function(response) {
          // Parse JSON string into object
            citymap = JSON.parse(response);
            console.log(citymap);

            // Construct the circle for each value in citymap.
            for (var city in citymap) {
                // Add the circle for this city to the map.
                var cityCircle = new google.maps.Circle({
                    strokeColor: '#FF0000',
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: '#FF0000',
                    fillOpacity: 0.35,
                    map: map,
                    center: citymap[city].coordinates,
                    radius: Math.sqrt(citymap[city].adj_du) * 100000
                });
            }
        });
    }

    //TODO: Could replace with jQuery if we decide to use, dont have to
    function loadJSON(callback) {
        
        var xobj = new XMLHttpRequest();
        xobj.overrideMimeType("application/json");
        xobj.open('GET', 'static/data/data2.json', true); // Replace 'my_data' with the path to your file
        xobj.onreadystatechange = function() {
            if (xobj.readyState == 4 && xobj.status == "200") {
                // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
                callback(xobj.responseText);
            }
        };
        xobj.send(null);
    }