var icon_url = '//cdn.rawgit.com/openlayers/ol3/master/examples/data/icon.png';
var vectorSource = new ol.source.Vector();
var vectorLayer = new ol.layer.Vector({
	source: vectorSource
});
var styles = {
	route: new ol.style.Style({
		stroke: new ol.style.Stroke({
			width: 6, color: [40, 40, 40, 0.8]
		})
	}),
  icon: new ol.style.Style({
    image: new ol.style.Icon({
      anchor: [0.5, 1],
      src: icon_url
    })
  })
};

var olMap = new ol.Map({
	layers: [
		new ol.layer.Tile({
			source: new ol.source.OSM()
		}),
		vectorLayer
	],
	view: new ol.View({
		center: ol.proj.transform([21.0004, 52.2261], 'EPSG:4326', 'EPSG:3857'),
		zoom: 7
	}),
	controls: ol.control.defaults({
		attributionOptions: {
			collapsible: false
		}
	})
});

init = function(document) {
	hideOverlay(document);
}

showOverlay = function(document) {
	let overlay = document.getElementById('myOverlay');
	let app = document.getElementById('myApp');

	overlay.style.display = 'block';
	app.style.display = 'inline-block';
}

hideOverlay = function(document) {
	let overlay = document.getElementById('myOverlay');
	let app = document.getElementById('myApp');

	overlay.style.display = 'none';
	app.style.display = 'block';
}

initMap = function(id) {
	olMap.setTarget(id);
}

var params = {
	LAYERS: 'pgrouting:pgrouting',
	FORMAT: 'image/png'
}

var startPoint = new ol.Feature();
var destPoint = new ol.Feature();

var finding = false;

var vectorLayer = new ol.layer.Vector({
	source: new ol.source.Vector({
		features: [startPoint, destPoint]
	})
});
olMap.addLayer(vectorLayer);

var transform = ol.proj.getTransform('EPSG:3857', 'EPSG:4326');

olMap.on('click', function(event) {
	if (startPoint.getGeometry() == null) {
		startPoint.setGeometry(new ol.geom.Point(event.coordinate));
	} else if (destPoint.getGeometry() == null) {
		destPoint.setGeometry(new ol.geom.Point(event.coordinate));

		var startCoord = transform(startPoint.getGeometry().getCoordinates());
		var destCoord = transform(destPoint.getGeometry().getCoordinates());
		var viewparams = {
			'start' : { 'x' : startCoord[0], 'y' : startCoord[1] },
			'end' : { 'x' : destCoord[0], 'y' : destCoord[1] }
		};
		params.viewparams = viewparams;
	}
});

initFindBtn = function(document) {
	var findButton = document.getElementById('find_path');
	findButton.addEventListener('click', function(event) {
		if(startPoint.getGeometry() == null) {
			alert("Define start point");
			return;
		}
		if(destPoint.getGeometry() == null) {
			alert("Define end point");
			return;
		}
		let timeInput = document.getElementById('time');
		console.log(timeInput);
		if(timeInput.value === "" || isNaN(timeInput.value)) {
			alert("Define additional time");
			return;
		}
		let distanceInput = document.getElementById('distance');
		if(distanceInput.value === "" || isNaN(distanceInput.value)) {
			alert("Define additional distance");
			return;
		}

		if(!finding) {
			finding = true;
			let time = parseInt(timeInput.value);
			let distance = parseInt(distanceInput.value);

			params.time = time;
			params.distance = distance;

			showOverlay(document);

			const Http = new XMLHttpRequest();
			const url='http://127.0.0.1:5000/find';
			Http.open("POST", url, true);
			Http.send(JSON.stringify(params));
			Http.onreadystatechange = function () {
				finding = false;
				if (Http.readyState === 4 && Http.status === 200) {
					var result = JSON.parse(Http.responseText);
					hideOverlay(document);

					// console.log(result);

					for(let point of result.key_points) {
						createFeature(point);
					}

					for(let path of result.route) {
						drawPath(path);
					}
				}
			};
		}
	});
}

initClearBtn = function(document) {
	var clearButton = document.getElementById('clear');
	clearButton.addEventListener('click', function(event) {
		startPoint.setGeometry(null);
		destPoint.setGeometry(null);
		vectorSource.clear();
	});
}

drawPath = function(points) {
	let locations = new Array();
	for(let point of points) {
		locations.push([point.x, point.y]);
	}

	var route = new ol.geom.LineString(locations).transform('EPSG:4326', 'EPSG:3857');

	var feature = new ol.Feature({
		type: 'route',
		geometry: route
	});

	feature.setStyle(styles.route);
	vectorSource.addFeature(feature);
}

createFeature = function(coord) {
  var feature = new ol.Feature({
    type: 'place',
    geometry: new ol.geom.Point(ol.proj.fromLonLat([coord.x, coord.y]))
  });
  feature.setStyle(styles.icon);
  vectorSource.addFeature(feature);
}
