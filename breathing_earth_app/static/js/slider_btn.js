var stop = 0;
document.querySelector("#play_btn").addEventListener("click", function() {
    var x = $("#slider").slider("value");
    stop = 1;
    // Called the function in each second
    var interval = setInterval(function() {
        $("#amount").val(x);
        $("#slider").slider('value', x);

        x++;
        if (x > 100 || stop == 0) {
            clearInterval(interval); // If exceeded 100, clear interval
        }
    }, 1500); // Run every 1.5 seconds
});

document.querySelector("#stop_btn").addEventListener("click", function() {
    stop = 0;
});

$('#clearTable').on('click', function(event, ui) {
    document.querySelector('#datatable').innerHTML = '<table id="datatable" class="text-center table table-striped"><thead><tr><th>GPS Name</th><th>Lat</th><th>Lng</th><th>Change (in meters)</th></tr></thead></table>';
});

$("#slider").slider().slider("pips", {
    last: false,
    rest: "label",
    step: 12,
    labels: ["2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016"]
});
