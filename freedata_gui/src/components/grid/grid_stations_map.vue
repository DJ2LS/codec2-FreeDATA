<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <div class="btn-group btn-group-sm" role="group">
        <button @click="zoomIn" class="btn btn-sm btn-outline-secondary"><i class="bi bi-plus-square"></i></button>
        <button @click="centerMap" class="btn btn-sm btn-secondary"><i class="bi bi-house-door"></i></button>
        <button @click="zoomOut" class="btn btn-sm btn-outline-secondary"><i class="bi bi-dash-square"></i></button>
        <span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
      </div>

      <div class="input-group input-group-sm ms-2">
        <input type="text" class="form-control w-100" placeholder="Station" aria-label="Username" aria-describedby="basic-addon1" v-model="infoText" disabled>
      </div>
    </div>
    <div class="card-body p-0">
      <div ref="mapContainer" class="map-container"></div>
      <div :style="popupStyle" class="popup">{{ infoText }}</div>
    </div>
  </div>
</template>

<script setup>
import { settingsStore as settings } from '../../store/settingsStore.js';
import { ref, onMounted, onBeforeUnmount, nextTick, toRaw } from 'vue';
import * as d3 from 'd3';
import { feature } from 'topojson-client';
import { locatorToLatLng, distance } from 'qth-locator';
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
import { useStateStore } from '../../store/stateStore.js';

// Activate Pinia
setActivePinia(pinia);
const state = useStateStore(pinia);

const mapContainer = ref(null);
const infoText = ref('');
const popupStyle = ref({});
let svg, path, projection, zoom;
const basePinRadius = 5; // Base radius for pins
let actualPinRadius = basePinRadius;

// Function to get distance between two grid squares
function getMaidenheadDistance(dxGrid) {
  try {
    return parseInt(distance(settings.remote.STATION.mygrid, dxGrid));
  } catch (e) {
    console.error('Error calculating distance:', e);
    return null;
  }
}

// Function to draw the map
const drawMap = () => {
  const containerWidth = mapContainer.value.clientWidth;
  const containerHeight = mapContainer.value.clientHeight;

  // Clear existing SVG if it exists
  if (svg) {
    svg.remove();
  }

  // Create Mercator projection
  projection = d3.geoMercator()
    .scale(containerWidth / (2 * Math.PI))
    .translate([containerWidth / 2, containerHeight / 2]);

  path = d3.geoPath().projection(projection);

  // Create SVG element
  svg = d3.select(mapContainer.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${containerWidth} ${containerHeight}`)
    .attr('preserveAspectRatio', 'xMidYMid meet');

  // Set up zoom behavior
  zoom = d3.zoom()
    .scaleExtent([1, 8])
    .on('zoom', (event) => {
      svg.selectAll('g').attr('transform', event.transform);

      // Adjust pin size and line width with zoom
      actualPinRadius = basePinRadius / event.transform.k;
      svg.selectAll('.my-pin').attr('r', actualPinRadius);
      svg.selectAll('.heard-pin').attr('r', actualPinRadius);

      svg.selectAll('.connection-line').attr('stroke-width', 1 / event.transform.k);
      svg.selectAll('.country-path').attr('stroke-width', 0.5 / event.transform.k);

      // Handle visibility of country labels based on zoom level
      if (event.transform.k < 3) {
        // Show only the largest country labels when zoomed out, hide regular labels
        svg.selectAll('.country-label').style('display', 'none');
        svg.selectAll('.largest-country-label').style('display', 'block');
      } else {
        // Show regular labels and hide largest country labels when zoomed in
        svg.selectAll('.country-label')
          .style('display', 'block')
          .attr('font-size', `${0.5 / event.transform.k}em`); // Smaller font size
        svg.selectAll('.largest-country-label').style('display', 'none');
      }
    });

  svg.call(zoom);

  // Import JSON data dynamically
  import('@/assets/countries-50m.json').then(worldData => {
    const countriesGeoJSON = feature(worldData, worldData.objects.countries);

    // Sort countries by area and select the top 10 largest
    const largestCountries = countriesGeoJSON.features
      .sort((a, b) => d3.geoArea(b) - d3.geoArea(a))
      .slice(0, 10);

    // Draw country paths
    const g = svg.append('g');


      // Add your own station's pin if mygrid is defined
  let mygrid = settings.remote.STATION.mygrid;
  if (mygrid) {
    const [myLat, myLng] = locatorToLatLng(mygrid);
    const [myX, myY] = projection([myLng, myLat]); // Correct projection for your location

    // Draw the pin for your station
    g.append('circle')
        .attr('class', 'my-pin')
        .attr('r', actualPinRadius + 2)
        .attr('fill', 'blue')
        .attr('cx', myX)
        .attr('cy', myY)
        .on('mouseover', () => {
          infoText.value = `Your Station - ${mygrid}`;
        })
        .on('mouseout', () => {
          infoText.value = '';
        });
  }


    g.selectAll('path')
      .data(countriesGeoJSON.features)
      .enter()
      .append('path')
      .attr('d', path)
      .attr('fill', '#ccc')
      .attr('stroke', '#333')
      .attr('stroke-width', 0.5);

    // Add labels for all countries
    g.selectAll('.country-label')
      .data(countriesGeoJSON.features)
      .enter()
      .append('text')
      .attr('class', 'country-label')
      .attr('transform', d => {
        const centroid = d3.geoCentroid(d);
        const [x, y] = projection(centroid);
        return `translate(${x}, ${y})`;
      })
      .attr('dy', '.35em')
      .attr('font-size', '0.4em') // Smaller initial font size
      .attr('text-anchor', 'middle')
      .text(d => d.properties.name)
      .style('display', 'none'); // Hide initially (will be shown when zoomed in)

    // Add labels for the largest countries
    g.selectAll('.largest-country-label')
      .data(largestCountries)
      .enter()
      .append('text')
      .attr('class', 'largest-country-label')
      .attr('transform', d => {
        const centroid = d3.geoCentroid(d);
        const [x, y] = projection(centroid);
        return `translate(${x}, ${y})`;
      })
      .attr('dy', '.35em')
      .attr('font-size', '0.6em') // Slightly smaller font size for visibility
      .attr('text-anchor', 'middle')
      .attr('fill', 'black')
      .text(d => d.properties.name);

    // Call the function to update pins and lines (including own location)
    updatePinsAndLines(g); // Use the g group element here
  });
};

// Function to update pins and draw lines
// Function to update pins and draw lines
const updatePinsAndLines = (g) => {
  // Remove existing pins and lines
  g.selectAll('.my-pin').remove();
  g.selectAll('.heard-pin').remove();
  g.selectAll('.connection-line').remove();

  const heardStations = toRaw(state.heard_stations); // Ensure it's the raw data
  const points = [];


  // Prepare points for heard stations
  heardStations.forEach(item => {
    if (
      item.gridsquare &&
      item.gridsquare.trim() !== '' &&
      item.gridsquare.trim() !== '------' &&
      item.origin
    ) {
      try {
        const [lat, lng] = locatorToLatLng(item.gridsquare);
        if (lat != null && lng != null) {
          points.push({ lat, lon: lng, origin: item.origin, gridsquare: item.gridsquare });
        }
      } catch (error) {
        console.error(`Error converting gridsquare ${item.gridsquare}:`, error);
      }
    }
  });


  // Add your own station's pin if mygrid is defined
  let mygrid = settings.remote.STATION.mygrid;
  if (mygrid) {
    const [myLat, myLng] = locatorToLatLng(mygrid);
    const [myX, myY] = projection([myLng, myLat]); // Correct projection for your location

    // Draw the pin for your station
    g.append('circle')
        .attr('class', 'my-pin')
        .attr('r', actualPinRadius + 2)
        .attr('fill', 'blue')
        .attr('cx', myX)
        .attr('cy', myY)
        .on('mouseover', () => {
          infoText.value = `Your Station - ${mygrid}`;
        })
        .on('mouseout', () => {
          infoText.value = '';
        });

    // Draw lines from your station to each heard station
    g.selectAll('.connection-line')
        .data(points)
        .enter()
        .append('line')
        .attr('class', 'connection-line')
        .attr('x1', myX)
        .attr('y1', myY)
        .attr('x2', d => projection([d.lon, d.lat])[0])
        .attr('y2', d => projection([d.lon, d.lat])[1])
        .attr('stroke', 'blue')
        .attr('stroke-width', 1)
        .attr('stroke-opacity', 0.5);
  }

  // Add pins for heard stations
  g.selectAll('.heard-pin')
      .data(points)
      .enter()
      .append('circle')
      .attr('class', 'heard-pin')
      .attr('r', actualPinRadius)
      .attr('fill', 'red')
      .attr('cx', d => projection([d.lon, d.lat])[0])
      .attr('cy', d => projection([d.lon, d.lat])[1])
      .on('mouseover', (event, d) => {
        infoText.value = `${d.origin} - ${d.gridsquare} (${getMaidenheadDistance(d.gridsquare)} km)`;
      })
      .on('mouseout', () => {
        infoText.value = '';
      });
};

// Center the map
const centerMap = () => {
  let mygrid = settings.remote.STATION.mygrid;
  if (!mygrid) {
    console.error('Error: Station grid square (mygrid) is not defined.');
    return;
  }

  const [lat, lng] = locatorToLatLng(mygrid);
  const [x, y] = projection([lng, lat]);

  // Ensure 'g' is selected before updating pins and lines
  const g = svg.select('g');
  updatePinsAndLines(g); // Update pins and lines based on the current state

  // Center the map to the station's coordinates
  svg.transition().duration(750).call(
      zoom.translateTo,
      x,
      y
  );
};

// Zoom in function
const zoomIn = () => {
  svg.transition().call(zoom.scaleBy, 1.2);
};

// Zoom out function
const zoomOut = () => {
  svg.transition().call(zoom.scaleBy, 0.8);
};

// Lifecycle hooks
onMounted(async () => {
  await nextTick();
  drawMap();
  window.addEventListener('resize', drawMap);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', drawMap);
});
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 400px;
}

.my-pin {
  fill: blue;
  stroke: black;
  stroke-width: 1px;
}

.heard-pin {
  fill: red;
  stroke: black;
  stroke-width: 1px;
}

.path {
  fill: #ccc;
  stroke: #333;
}

.connection-line {
  stroke: red;
  stroke-width: 1;
  stroke-opacity: 0.5;
}

.popup {
  background-color: white;
  border: 1px solid black;
  padding: 5px;
  position: absolute;
  display: none;
  z-index: 10;
  pointer-events: none;
}
</style>
