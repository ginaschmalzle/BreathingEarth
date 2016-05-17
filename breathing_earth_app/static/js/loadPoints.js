    var coordlist = {};
    var datelist = {};

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


        loadInitialPoints(function(response) {
            coordlist = JSON.parse(response);
            //console.log(coordlist);
            var datatablecount = 0;
            
            for (var loc in coordlist) {
                //console.log('loc: ' + loc +' lat: '+coordlist[loc].lat + ' lng: '+coordlist[loc].lng);
                // Add the circle for this city to the map.
                var cityCircle = new google.maps.Circle({
                    strokeColor: '#FF0000',
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: '#FF0000',
                    fillOpacity: 0.35,
                    map: map,
                    center: coordlist[loc], //.coordinates,
                    radius: 10000 //Math.sqrt(citymap[city].adj_du) * 100000
                });
                if(datatablecount <= 10) {
                    $('#datatable').append("<tr><td>"+loc+"</td><td>"+coordlist[loc].lat+"</td><td>"+coordlist[loc].lng+"</td></tr>");
                    datatablecount++;
                }
                
            }
            

        });      


        /*loadChanges(function(response) {
          // Parse JSON string into object
            datelist = JSON.parse(response);
            console.log(datelist);

            // Construct the circle for each value in citymap.
            for (var dates in datelist) {
                console.log(dates);
                for(var sat in datelist[dates]) {
                    console.log('sat: '+sat + ' | value: '+datelist[dates][sat]);
                }
            };
        });
        */
         /*
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
        */
    }

    //TODO: Could replace with jQuery if we decide to use, dont have to
    function loadInitialPoints(callback) {
        
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

    function loadChanges(callback) {
        
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