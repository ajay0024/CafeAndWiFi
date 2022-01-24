var locations = [];
var map, infobox;
var gsAPIKey = "AIzaSyDrqsigRRdZc0XVmuNchPiXLF6GpvDV3Hk"
var cx = "4d965549728e9d13c"
$(document).ready(function(dataoptions) {
  var error = GetURLParameter("error");
  if (error == "login") {
    new bootstrap.Modal($("#loginModal")).show()
  } else if (error == "registration") {
    console.log("hi")
    new bootstrap.Modal($("#registrationModal")).show()
  }
  filters_function()
  let map;
  update_places()
  add_filters()
  updateLocation()
  if($("#searchResultName").val() && $("#searchResultCity").val()){
    loadImages($("#searchResultName").val(), $("#searchResultCity").val())
  }

});

function GetURLParameter(sParam) {
  var sPageURL = window.location.search.substring(1);
  var sURLVariables = sPageURL.split('&');
  for (var i = 0; i < sURLVariables.length; i++) {
    var sParameterName = sURLVariables[i].split('=');
    if (sParameterName[0] == sParam) {
      return sParameterName[1];
    }
  }
}

function filters_function() {

  let filters = $(".prod_filters").find(".btn")
  console.log(filters)
  places = $(".places").children()
  filters.click(function() {
    $(this).toggleClass("active");
    places.show();
    console.log(filters)
    filters.each(function() {
      state = $(this).hasClass("active");
      console.log("juo")
      filter = $(this).attr("data-filter");
      places.each(function() {
        if (state && $(this).attr(filter) != "True") {
          $(this).hide()
        }
      })
    });
    update_places_count()
    update_places()
  });

}

function add_filters() {
  let filters = $("#filters").find(".btn")
  filters.each(function(){
    if ($(this).find("input").val() == "True"){
      $(this).toggleClass("active");
    }
  })
  filters.click(function() {
    $(this).toggleClass("active");
    filters.each(function() {
      state = $(this).hasClass("active");
      if(state){
        $(this).find("input").val("True");
      }
      else{
        $(this).find("input").val("True");
      }
    });
  });

}

function update_places_count() {
  places = $(".places").children();
  total_places = places.length
  remaining_places = total_places
  places.each(function() {
    if ($(this).is(":hidden")) {
      remaining_places -= 1
    }
  })
  if (remaining_places == total_places) {
    text = remaining_places
  } else {
    text = remaining_places + "/" + total_places
  }
  $("#cafes-count").html(text)
}

function update_places() {
  places = $(".places").children()
  let index = 1
  places.each(function() {
    url = $(this).attr("data-map_url")
    id = $(this).attr("data-id")
    lat = $(this).attr("data-lat")
    long = $(this).attr("data-long")
    cname = $(this).find(".cafe-name").html()
    console.log(url + lat)
    if (lat == "None") {
      $.post("../convertURL", {
          "url": url,
          "id": id
        }, function(data) {
          console.log(data);
        })
        .done(function() {
          console.log("pass")
        })
        .fail(function() {
          console.log("fail")
        })
    } else {
      let loc = [lat, long, cname, index]
      locations.push(loc)
      index += 1
    }
  });
}

function GetMap() {
  map = new Microsoft.Maps.Map('#map', {
    credentials: 'AnL8qq7Xiki_iadsL8PKYOSfE5nQP1zQIrXDU8yUh-xf8lHDdVIf_8iHR3yn_zwz',
    center: new Microsoft.Maps.Location(51.50632, -0.12714),
    mapTypeId: Microsoft.Maps.MapTypeId.road,
    zoom: 12
  });
  // Map in case of view_cafe page
  if ($("#cafe").attr("data-lat") && $("#cafe").attr("data-long")) {
    lat=$("#cafe").attr("data-lat")
    long=$("#cafe").attr("data-long")
    name=$("#cafe-name").html()
    address=$("#cafe").attr("data-address")

    map.setView ({
      mapTypeId: Microsoft.Maps.MapTypeId.road,
      center: new Microsoft.Maps.Location(lat, long),
      zoom: 15
    });
    let pin = new Microsoft.Maps.Pushpin(new Microsoft.Maps.Location(lat, long), {
      title: name,
      text: address,
    });
    pin.metadata = {
      title: name,
      text: address,
    };
    map.entities.push(pin);
  }

  infobox = new Microsoft.Maps.Infobox(map.getCenter(), {
    visible: false
  });

  pins = []
  locs = []
  places = $(".places").children()
  index = 1
  places.each(function() {
    lat = $(this).attr("data-lat")
    long = $(this).attr("data-long")
    name = $(this).find(".cafe-name").html()
    icons = $(this).find(".facilities").html()
    locs.push(new Microsoft.Maps.Location(lat, long))
    let pin = new Microsoft.Maps.Pushpin(new Microsoft.Maps.Location(lat, long), {
      title: name,
      text: index,
    });
    pin.metadata = {
      title: name,
      description: icons
    };
    index += 1
    map.entities.push(pin);
    Microsoft.Maps.Events.addHandler(pin, 'click', pushpinClicked);
  });
  if (locs.length > 0) {
    var rect = Microsoft.Maps.LocationRect.fromLocations(locs);
    map.setView({
      bounds: rect,
      padding: 80
    });
  }
  if ($("#searchBox").length) {
    Microsoft.Maps.loadModule('Microsoft.Maps.AutoSuggest', function() {
      var manager = new Microsoft.Maps.AutosuggestManager({
        map: map,
        businessSuggestions: true
      });
      manager.attachAutosuggest('#searchBox', '#searchBoxContainer', selectedSuggestion);
    });
  }


}

function selectedSuggestion(result) {

  //Remove previously selected suggestions from the map.
  map.entities.clear();

  //Show the suggestion as a pushpin and center map over it.
  var pin = new Microsoft.Maps.Pushpin(result.location);
  map.entities.push(pin);
  map.setView({
    bounds: result.bestView
  });
  console.log(result)
  $("#searchResultName").val(result.title);
  $("#searchResultAddress").val(result.address.addressLine);
  $("#searchResultCity").val(result.address.locality);
  $("#searchResultCountry").val(result.address.countryRegion);
  $("#searchResultLat").val(result.location.latitude);
  $("#searchResultLong").val(result.location.longitude);
  loadImages(result.title , result.address.locality)


}

function loadImages(title, locality){
  url = "https://www.googleapis.com/customsearch/v1?key=" + gsAPIKey + "&cx=" + cx + "&q=" + title + ", " + locality + "&searchType=image"

  var jqxhr = $.get(url, function(data) {
      console.log(data);
      $("#image-selection .img-container").each(function(i) {
        $(this).empty();
        $(this).prepend('<img class="unselected" src="' + data.items[i].link + '" alt="Loading Image.." width="100%" >');
      });

      $(".img-container:first img").addClass("selected")
      $('input[name="image-link"]').val($(".img-container:first img").attr("src"))
    })
    .done(function() {
      imageLinkElem = $('input[name="image-link"]')
      $(".d-none").removeClass("d-none");
      $("#filters").removeClass("d-none");
      images = $(".img-container img")
      images.click(function() {
        images.removeClass("selected")
        images.addClass("unselected")
        $(this).removeClass("unselected")
        $(this).addClass("selected")
        // Update image-link in form
        imageLinkElem.val($(this).attr("src"))
      })
    })
    .fail(function() {
      $("#image-selection").addClass("hidden");
      alert("Error: Could not load Images");
    })
    .always(function() {
      console.log("finished");
    });
}

function pushpinClicked(e) {
  console.log("Pin Pushed")
  //Make sure the infobox has metadata to display.
  if (e.target.metadata) {
    console.log(e.target.metadata.title)
    //Set the infobox options with the metadata of the pushpin.
    infobox.setOptions({
      location: e.target.getLocation(),
      title: e.target.metadata.title,
      description: e.target.metadata.description,
      visible: true
    });
    infobox.setMap(map)
  }
}

function updateLocation() {

}
