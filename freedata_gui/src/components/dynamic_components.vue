<script setup>
import { ref, onMounted, nextTick, shallowRef, render, h } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import "../../node_modules/gridstack/dist/gridstack.min.css";
import { GridStack } from "gridstack";
import { useStateStore } from "../store/stateStore.js";
const state = useStateStore(pinia);
import { setRadioParametersFrequency } from "../js/api";
import { saveLocalSettingsToConfig, settingsStore } from "../store/settingsStore";

import active_heard_stations from "./grid/grid_active_heard_stations.vue";
import mini_heard_stations from "./grid/grid_active_heard_stations_mini.vue";
import active_stats from "./grid/grid_active_stats.vue";
import active_audio_level from "./grid/grid_active_audio.vue";
import active_rig_control from "./grid/grid_active_rig_control.vue";
import active_broadcasts from "./grid/grid_active_broadcasts.vue";
import active_broadcasts_vert from "./grid/grid_active_broadcasts_vert.vue";
import s_meter from "./grid/grid_s-meter.vue";
import dbfs_meter from "./grid/grid_dbfs.vue";
import grid_activities from "./grid/grid_activities.vue";
import grid_button from "./grid/grid_button.vue";
import grid_ptt from "./grid/grid_ptt.vue";
import grid_mycall from "./grid/grid_mycall.vue";
import grid_stop from "./grid/grid_stop.vue";
import grid_tune from "./grid/grid_tune.vue";
import grid_CQ_btn from "./grid/grid_CQ.vue";
import grid_ping from "./grid/grid_ping.vue";
import grid_freq from "./grid/grid_frequency.vue";
import grid_beacon from "./grid/grid_beacon.vue";
import grid_mycall_small from "./grid/grid_mycall small.vue";
import grid_scatter from "./grid/grid_scatter.vue";
import grid_stats_chart from "./grid/grid_stats_chart.vue";
import grid_swr_meter from "./grid/grid_swr_meter.vue";
import grid_stations_map from "./grid/grid_stations_map.vue";

let count = ref(0);
let grid = null; // DO NOT use ref(null) as proxies GS will break all logic when comparing structures... see https://github.com/gridstack/gridstack.js/issues/2115
let items = ref([]);
class gridWidget {
  //Contains the vue component
  component2;
  //Initial size and location if autoplace is false
  size;
  //Text for button label in widget picker
  text;
  //if true add when quick fill button is clicked
  quickFill;
  //Auto place; true to add where ever it fits; false uses position information
  autoPlace;
  //Category to place widget in widget picker
  category;
  //Unique ID for widget
  id;
  //if true add when quick fill (small) button is clicked
  quickFillSM;
  //Initial size and location if autoplace is false and using small quick fill
   sizeSM;
  constructor(component, size, text, quickfill, autoPlace, category, id, quickFillSM, sizeSM) {
    this.component2 = component;
    this.size = size;
    this.text = text;
    this.quickFill = quickfill;
    this.autoPlace = autoPlace;
    this.category = category;
    this.id = id;
    this.quickFillSM = quickFillSM;
    this.sizeSM = sizeSM
  }
}

//Array of grid widgets
//Order can be changed so sorted correctly, but do not change ID as it'll affect saved configs
const gridWidgets = [
  new gridWidget(
    grid_activities,
    { x: 0, y: 53, w: 6, h: 55 },
    "Activities list",
    true,
    true,
    "Activity",
    8,
    false,
    { x: 0, y: 53, w: 6, h: 55 }
  ),
  new gridWidget(
    active_heard_stations,
    { x: 0, y: 13, w: 16, h: 40 },
    "Heard stations list (detailed)",
    true,
    true,
    "Activity",
    0,
    false,
    { x: 0, y: 53, w: 6, h: 55 }
  ),
  new gridWidget(
    grid_scatter,
    { x: 0, y: 114, w: 6, h: 30 },
    "Scatter graph",
    false,
    true,
    "Stats",
    19,
    false,
    { x: 0, y: 53, w: 6, h: 55 }
  ),
  new gridWidget(
    grid_stats_chart,
    { x: 0, y: 114, w: 6, h: 30 },
    "Speed/SNR graph",
    false,
    true,
    "Stats",
    20,
    false,
    { x: 0, y: 114, w: 6, h: 30 }
  ),
  new gridWidget(
    active_stats,
    { x: 16, y: 16, w: 8, h: 87 },
    "Stats (waterfall, etc)",
    true,
    true,
    "Stats",
    1,
    true,
    { x: 12, y: 0, w: 12, h: 56 }
  ),
  new gridWidget(
    active_audio_level,
    { x: 16, y: 0, w: 8, h: 20 },
    "Audio main",
    false,
    true,
    "Audio",
    2,
    false,
    { x: 0, y: 114, w: 6, h: 20 }
  ),
  new gridWidget(
    grid_freq,
    { x: 20, y: 8, w: 4, h: 8 },
    "Frequency widget",
    true,
    true,
    "Rig",
    14,
    false,
    { x: 0, y: 114, w: 6, h: 30 }
  ),
  new gridWidget(
    active_rig_control,
    { x: 0, y: 108, w: 6, h: 25 },
    "Rig control main",
    true,
    true,
    "Rig",
    3,
    false,
    { x: 0, y: 114, w: 6, h: 25 }
  ),
  new gridWidget(
    grid_beacon,
    { x: 3, y: 27, w: 3, h: 8 },
    "Beacon button",
    false,
    true,
    "Broadcasts",
    16,
    true,
    { x: 0, y: 14, w: 12, h: 14 }
  ),
  new gridWidget(
    active_broadcasts,
    { x: 6, y: 70, w: 6, h: 25 },
    "Broadcasts main (horizontal)",
    false,
    true,
    "Broadcasts",
    4,
    false,
    { x: 6, y: 70, w: 6, h: 25 }
  ),
  new gridWidget(
    mini_heard_stations,
    { x: 1, y: 1, w: 6, h: 54 },
    "Heard stations list (small)",
    false,
    true,
    "Activity",
    5,
    true,
    { x: 0, y: 42, w: 12, h: 42 }
  ),
  new gridWidget(
    s_meter,
    { x: 16, y: 0, w: 4, h: 8 },
    "S-Meter widget",
    true,
    true,
    "Rig",
    6,
    false,
    { x: 16, y: 0, w: 4, h: 8 }
  ),
  new gridWidget(
    grid_swr_meter,
    { x: 16, y: 8, w: 4, h: 8 },
    "SWR widget",
    true,
    true,
    "Rig",
    21,
    false,
    { x: 16, y: 8, w: 4, h: 8 }
  ),
  new gridWidget(
    dbfs_meter,
    { x: 20, y: 0, w: 4, h: 8 },
    "Dbfs meter",
    true,
    true,
    "Audio",
    7,
    false,
    { x: 20, y: 0, w: 4, h: 8 }
  ),
  new gridWidget(
    active_broadcasts_vert,
    { x: 16, y: 103, w: 8, h: 42 },
    "Broadcasts main (vertical)",
    true,
    true,
    "Broadcasts",
    9,
    false,
    { x: 16, y: 103, w: 8, h: 42 }
  ),
  new gridWidget(
    grid_ptt,
    { x: 2, y: 0, w: 5, h: 13 },
    "Tx/PTT indicator",
    true,
    true,
    "Rig",
    10,
    true,
    { x: 5, y: 0, w: 7, h: 14 }
  ),
  new gridWidget(
    grid_mycall,
    { x: 7, y: 0, w: 9, h: 13 },
    "My callsign widget",
    true,
    true,
    "Other",
    11,
    false,
    { x: 7, y: 0, w: 9, h: 13 }
  ),
  new gridWidget(
    grid_mycall_small,
    { x: 8, y: 40, w: 4, h: 10 },
    "My callsign widget (small)",
    false,
    true,
    "Other",
    17,
    false,
    { x: 8, y: 40, w: 4, h: 8 }
  ),
  new gridWidget(
    grid_CQ_btn,
    { x: 3, y: 27, w: 2, h: 8 },
    "CQ button",
    false,
    true,
    "Broadcasts",
    12,
    true,
    { x: 0, y: 28, w: 12, h: 14 }
  ),
  new gridWidget(
    grid_ping,
    { x: 3, y: 27, w: 4, h: 9 },
    "Ping widget",
    false,
    true,
    "Broadcasts",
    13,
    true,
    { x: 0, y: 84, w: 12, h: 9 }
  ),
  new gridWidget(
    grid_stations_map,
    { x: 6, y: 53, w: 10, h: 92 },
    "Station Map",
    true,
    true,
    "Other",
    22,
    true,
    { x: 12, y: 56, w: 12, h: 92 }
  ),
  new gridWidget(
    grid_stop,
    { x: 0, y: 0, w: 2, h: 13 },
    "Stop widget",
    true,
    true,
    "Other",
    15,
    true,
    { x: 0, y: 0, w: 5, h: 14 }
  ),
  new gridWidget(
    grid_tune,
    { x: 16, y: 8, w: 2, h: 8 },
    "Tune widget",
    false,
    true,
    "Audio",
    18,
    false,
    { x: 16, y: 8, w: 2, h: 8 }
  )
  //Next new widget ID should be 23
];

function updateFrequencyAndApply(frequency) {
  state.new_frequency = frequency;
  set_radio_parameter_frequency();
}

function set_radio_parameter_frequency(){
  setRadioParametersFrequency(state.new_frequency);
}
/*
function set_radio_parameter_mode(){
  setRadioParametersMode(state.mode);
}

function set_radio_parameter_rflevel(){
  setRadioParametersRFLevel(state.rf_level);
}
*/

function savePreset() {
  settingsStore.local.grid_preset = settingsStore.local.grid_layout;
  console.log("Saved grid preset");
}

function loadPreset() {
  clearAllItems();
  settingsStore.local.grid_layout = settingsStore.local.grid_preset;
  restoreGridLayoutFromConfig();
  console.log("Restored grid preset");
}

function onChange(event, changeItems) {
  if (changeItems) {
    changeItems.forEach((item) => {
      const widget = items.value.find((w) => w.id === item.id);
      if (widget) {
        Object.assign(widget, item);
      }
    });
    saveGridLayout();
  }
}

function restoreGridLayoutFromConfig() {
  if (items.value.length === 0) {
    const savedGrid = JSON.parse(settingsStore.local.grid_layout || "[]");
    savedGrid.forEach(([x, y, w, h, id]) => {
      const widget = gridWidgets.find((gw) => gw.id === id);
      if (widget) {
        const backupSize = widget.size;
        widget.autoPlace = false;
        widget.size = { x, y, w, h };
        addNewWidget2(widget, false);
        widget.autoPlace = true;
        widget.size = backupSize;
      }
    });
  }
}

function saveGridLayout() {
  const cfg = items.value.map((item) => {
    const widget = gridWidgets.find((gw) => gw.component2.__name === item.component2.__name);
    const widgetId = widget ? widget.id : -1;
    return [item.x, item.y, item.w, item.h, widgetId];
  });
  settingsStore.local.grid_layout = JSON.stringify(cfg);
  saveLocalSettingsToConfig();
}

function addNewWidget2(componentToAdd, saveToConfig) {
  const node = { ...componentToAdd.size, id: `w_${count.value++}`, component2: shallowRef(componentToAdd.component2), autoPlace: componentToAdd.autoPlace };
  items.value.push(node);
  nextTick(() => {
    grid?.makeWidget(node.id);
    if (saveToConfig) saveGridLayout();
  });
}
function addNewWidget2SM(componentToAdd, saveToConfig) {
  const node = { ...componentToAdd.sizeSM, id: `w_${count.value++}`, component2: shallowRef(componentToAdd.component2), autoPlace: componentToAdd.autoPlace };
  items.value.push(node);
  nextTick(() => {
    grid?.makeWidget(node.id);
    if (saveToConfig) saveGridLayout();
  });
}
function remove(widget) {
  const index = items.value.findIndex((w) => w.id === widget.id);
  if (index !== -1) {
    items.value.splice(index, 1);
    grid?.removeWidget(`#${widget.id}`, false);
    saveGridLayout();
  }
}

function toggleGridEdit() {
  settingsStore.local.grid_enabled = !settingsStore.local.grid_enabled;
  setGridEditState();
}

function setGridEditState() {
  settingsStore.local.grid_enabled ? grid?.enable() : grid?.disable();
}

function clearAllItems() {
  grid?.removeAll(false);
  count.value = 0;
  items.value = [];
  saveGridLayout();
}

function quickfill() {
  gridWidgets.forEach((gw) => {
    if (gw.quickFill) {
      gw.autoPlace = false;
      addNewWidget2(gw, false);
      gw.autoPlace = true;
    }
  });
  saveGridLayout();
}
function quickfillSM() {
  gridWidgets.forEach((gw) => {
    if (gw.quickFillSM) {
      gw.autoPlace = false;
      addNewWidget2SM(gw, false);
      gw.autoPlace = true;
    }
  });
  saveGridLayout();
}
onMounted(() => {
  grid = GridStack.init({
    float: true,
    cellHeight: "5px",
    minRow: 50,
    margin: 5,
    column: 24,
    draggable: { scroll: true },
    resizable: { handles: "se,sw" }
  });

  /*//Do not delete, aids in adjusting widget fill locations
  grid?.on("dragstop", (event, element) => {
    const node = element.gridstackNode;
    console.info(`Moved #${node.id} to ${node.x},${node.y}. Dimensions: ${node.w}x${node.h}`);
  });*/

  grid?.on("change", onChange);

  gridWidgets.forEach((gw) => {
    const domId = `${gw.category.toLowerCase()}Body`;
    const dom = document.getElementById(domId);
    if (dom) {
      const index = gridWidgets.findIndex((w) => w.text === gw.text);
      dom.insertAdjacentHTML("beforeend", `<div id="gridbtn-${index}"></div>`);
      const dom2 = document.getElementById(`gridbtn-${index}`);
      if (dom2) {
        const vueComponent = h(grid_button, { btnText: gw.text, btnID: index });
        render(vueComponent, dom2);
      }
    }
  });

  restoreGridLayoutFromConfig();

  if (items.value.length === 0) {
    console.info("Grid config is empty; using default");
    quickfill();
  }

  window.addEventListener("add-widget", (event) => {
    const evt = event;
    addNewWidget2(gridWidgets[evt.detail], true);
  });
  setGridEditState();
});
</script>

<template>
  <button
    class="btn btn-secondary fixed-middle-right rounded-0 rounded-start-4 p-1 pt-4 pb-4"
    type="button"
    data-bs-toggle="offcanvas"
    data-bs-target="#offcanvasGridItems"
    aria-controls="offcanvasGridItems"
  >
   <!-- <i class="bi bi-grip-vertical h5">      </i>-->

  <span class="me-4 text-white" style="writing-mode: vertical-rl; transform: rotate(180deg);">
    grid edit
  </span>


  </button>

  <div class="grid-container z-0" style="height: calc(100vh - 51px);">
    <div class="grid-stack z-0">
      <div
        v-for="(w) in items"
        class="grid-stack-item"
        :gs-x="w.x"
        :gs-y="w.y"
        :gs-w="w.w"
        :gs-h="w.h"
        :gs-id="w.id"
        :id="w.id"
        :key="w.id"
        :gs-auto-position="w.autoPlace"
      >
        <div class="grid-stack-item-content">
          <button
            @click="remove(w)"
            class="btn-close grid-stack-floaty-btn"
            :class="settingsStore.local.grid_enabled === true ? 'visible':'invisible'"
          ></button>
          <component :is="w.component2" />
        </div>
      </div>
    </div>
  </div>

  <div
    class="offcanvas offcanvas-end"
    data-bs-scroll="true"
    data-bs-backdrop="true"
    tabindex="-1"
    id="offcanvasGridItems"
    aria-labelledby="offcanvasGridItemsLabel"
  >
    <div class="offcanvas-header">
      <h5 class="offcanvas-title" id="offcanvasGridItemsLabel">
        Manage grid widgets &nbsp;<button
        class="btn btn-sm"
        :class="settingsStore.local.grid_enabled == true ? 'btn-outline-success' : 'btn-outline-danger'"
        type="button"
        @click="toggleGridEdit"
        title="Lock/unloack changes to grid"
      >
        <i class="bi" :class="settingsStore.local.grid_enabled == true ? 'bi-unlock-fill' : 'bi-lock-fill'"></i>
      </button>&nbsp;
      </h5>

      <button
        type="button"
        class="btn-close"
        data-bs-dismiss="offcanvas"
        aria-label="Close"
      ></button>
    </div>
    <div class="offcanvas-body">
      <p>
        Grid widgets allow you to customize the display. You may add additional widgets to fit your needs. You can move and resize the individual widgets!
      </p>
      <div>
        <button
          class="btn btn-outline-primary mb-2"
          type="button"
          @click="quickfill"
        >
          Fill grid with common widgets
        </button>
        <button
          class="btn btn-outline-primary"
          type="button"
          @click="quickfillSM"
        >
          Fill grid for small screens
        </button>
      </div>
      <hr />
      <!-- Begin widget selector -->
      <div class="accordion" id="accordionExample">
        <!-- Heard Stations -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingHeardStations">
            <button
              class="accordion-button"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseHeardStations"
              aria-expanded="true"
              aria-controls="collapseHeardStations"
            >
              <strong>Activity</strong>
            </button>
          </h2>
          <div
            id="collapseHeardStations"
            class="accordion-collapse collapse show"
            aria-labelledby="headingHeardStations"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="activityBody"></div>
          </div>
        </div>

        <!-- Activities -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingActivities">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseActivities"
              aria-expanded="false"
              aria-controls="collapseActivities"
            >
              <strong>Audio</strong>
            </button>
          </h2>
          <div
            id="collapseActivities"
            class="accordion-collapse collapse"
            aria-labelledby="headingActivities"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="audioBody"></div>
          </div>
        </div>
        <!-- Broadcasts -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingBroadcasts">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseBroadcasts"
              aria-expanded="false"
              aria-controls="collapseBroadcasts"
            >
              <strong>Broadcasts</strong>
            </button>
          </h2>
          <div
            id="collapseBroadcasts"
            class="accordion-collapse collapse"
            aria-labelledby="headingBroadcasts"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="broadcastsBody"></div>
          </div>
        </div>
        <!-- Radio Control -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingRadioControl">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseRadioControl"
              aria-expanded="false"
              aria-controls="collapseRadioControl"
            >
              <strong>Radio Control/Status</strong>
            </button>
          </h2>
          <div
            id="collapseRadioControl"
            class="accordion-collapse collapse"
            aria-labelledby="headingRadioControl"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="rigBody"></div>
          </div>
        </div>

        <!-- Audio Control -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingAudioControl">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseAudioControl"
              aria-expanded="false"
              aria-controls="collapseAudioControl"
            >
              <strong>Statistics</strong>
            </button>
          </h2>
          <div
            id="collapseAudioControl"
            class="accordion-collapse collapse"
            aria-labelledby="headingAudioControl"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="statsBody"></div>
          </div>
        </div>

        <!-- Statistics -->
        <div class="accordion-item">
          <h2 class="accordion-header" id="headingStatistics">
            <button
              class="accordion-button collapsed"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#collapseStatistics"
              aria-expanded="false"
              aria-controls="collapseStatistics"
            >
              <strong>Other</strong>
            </button>
          </h2>
          <div
            id="collapseStatistics"
            class="accordion-collapse collapse"
            aria-labelledby="headingStatistics"
            data-bs-parent="#accordionExample"
          >
            <div class="accordion-body" id="otherBody"></div>
          </div>
        </div>
      </div>
      <hr />
      <button
        class="btn btn-sm btn-outline-warning"
        type="button"
        @click="clearAllItems"
        title="Clear all items from the grid"
      >
        Clear grid
      </button>
      <hr/>
      <button
        class="btn btn-sm btn-outline-dark"
        type="button"
        @click="loadPreset"
        title="Restore your saved grid preset (clears current grid)"
      >

        Restore preset
      </button>&nbsp;
      <button
        class="btn btn-sm btn-outline-dark"
        type="button"
        @click="savePreset"
        title="Save current grid layout as a preset that can be restored using restore preset button"
      >
        Save preset
      </button>
    </div>
  </div>

  <div class="offcanvas offcanvas-end text-start"     data-bs-scroll="true"
    data-bs-backdrop="false" tabindex="-1" id="offcanvasFrequency" aria-labelledby="offcanvasExampleLabel">
  <div class="offcanvas-header">
    <h5 class="offcanvas-title" id="offcanvasExampleLabel">Frequency selection</h5>
      <button
        type="button"
        class="btn-close"
        data-bs-dismiss="offcanvas"
        aria-label="Close"
      ></button>



  </div>
  <div class="offcanvas-body">
    <p>
    Commonly used frequencies are listed here, and are all USB.&nbsp; Simply click on a entry or manually enter a frequency in the textbox to tune your rig if rig control is enabled.
    </p>
    <ul
              class="list-group"
              aria-labelledby="dropdownMenuButton"
              style="z-index: 50"
            >
              <li class="list-group-item">
                <div class="input-group p-1">
                  <span class="input-group-text">frequency</span>
                  <input
                    v-model="state.new_frequency"
                    style="max-width: 8rem"
                    pattern="[0-9]*"
                    type="text"
                    class="form-control form-control-sm"
                    v-bind:class="{
                      disabled: state.hamlib_status === 'disconnected',
                    }"
                    placeholder="Type frequency..."
                    aria-label="Frequency"
                  />
                  <button
                    class="btn btn-sm btn-outline-success"
                    type="button"
                    @click="updateFrequencyAndApply(state.new_frequency)"
                    v-bind:class="{
                      disabled: state.hamlib_status === 'disconnected',
                    }"
                  >
                    <i class="bi bi-check-square"></i>
                  </button>
                </div>
              </li>

              <!-- Dropdown Divider -->
              <li class="list-group-item"><hr class="dropdown-divider" /></li>
              <!-- Dropdown Items -->
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(50616000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">50.616 MHz</h5>
      <small>EU / US</small>
      <h6>6m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(50308000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">50.308 MHz</h5>
      <small>US</small>
      <h6>6m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(28093000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">28.093 MHz</h5>
      <small>EU / US</small>
      <h6>10m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(27265000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">27.265 MHz</h5>
      <small>Ch 26</small>
      <h6>11m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(27245000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">27.245 MHz</h5>
      <small>Ch 25</small>
      <h6>11m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(24908000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">24.908 MHz</h5>
      <small>EU / US</small>
      <h6>12m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(21093000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">21.093 MHz</h5>
      <small>EU / US</small>
      <h6>15m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(18106000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">18.106 MHz</h5>
      <small>EU / US</small>
      <h6>17m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(14093000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">14.093 MHz</h5>
      <small>EU / US</small>
      <h6>20m</h6>
    </div>
  </a>
  <a href="#" class="list-group-item list-group-item-action" @click="updateFrequencyAndApply(7053000)">
    <div class="d-flex w-100 justify-content-between">
      <h5 class="mb-1">7.053 MHz</h5>
      <small>EU / US</small>
      <h6>40m</h6>
    </div>
  </a>
            </ul>
  </div>
</div>

</template>

<style>
.fixed-middle-right {
  position: fixed; /* Fixed/sticky position */
  top: 50%; /* Position at the middle of the viewport */
  right: 0px; /* Place the button 20px from the right */
  transform: translateY(-50%); /* Adjust for exact vertical centering */
  z-index: 999; /* Ensure it's on top of other elements */
}

.grid-stack-item {
  text-align: center;
  overflow: auto;
  z-index: 50;
}
.grid-stack-floaty-btn {
  position: absolute;
  right: 2px;
  z-index: 1000;
  float: right;
  top: 4px;
}
.grid-container {
  overflow-y: auto;
}
.gs-24 > .grid-stack-item {
  width: 4.167%;
}
.gs-24 > .grid-stack-item[gs-x="1"] {
  left: 4.167%;
}
.gs-24 > .grid-stack-item[gs-w="2"] {
  width: 8.333%;
}
.gs-24 > .grid-stack-item[gs-x="2"] {
  left: 8.333%;
}
.gs-24 > .grid-stack-item[gs-w="3"] {
  width: 12.5%;
}
.gs-24 > .grid-stack-item[gs-x="3"] {
  left: 12.5%;
}
.gs-24 > .grid-stack-item[gs-w="4"] {
  width: 16.667%;
}
.gs-24 > .grid-stack-item[gs-x="4"] {
  left: 16.667%;
}
.gs-24 > .grid-stack-item[gs-w="5"] {
  width: 20.833%;
}
.gs-24 > .grid-stack-item[gs-x="5"] {
  left: 20.833%;
}
.gs-24 > .grid-stack-item[gs-w="6"] {
  width: 25%;
}
.gs-24 > .grid-stack-item[gs-x="6"] {
  left: 25%;
}
.gs-24 > .grid-stack-item[gs-w="7"] {
  width: 29.167%;
}
.gs-24 > .grid-stack-item[gs-x="7"] {
  left: 29.167%;
}
.gs-24 > .grid-stack-item[gs-w="8"] {
  width: 33.333%;
}
.gs-24 > .grid-stack-item[gs-x="8"] {
  left: 33.333%;
}
.gs-24 > .grid-stack-item[gs-w="9"] {
  width: 37.5%;
}
.gs-24 > .grid-stack-item[gs-x="9"] {
  left: 37.5%;
}
.gs-24 > .grid-stack-item[gs-w="10"] {
  width: 41.667%;
}
.gs-24 > .grid-stack-item[gs-x="10"] {
  left: 41.667%;
}
.gs-24 > .grid-stack-item[gs-w="11"] {
  width: 45.833%;
}
.gs-24 > .grid-stack-item[gs-x="11"] {
  left: 45.833%;
}
.gs-24 > .grid-stack-item[gs-w="12"] {
  width: 50%;
}
.gs-24 > .grid-stack-item[gs-x="12"] {
  left: 50%;
}
.gs-24 > .grid-stack-item[gs-w="13"] {
  width: 54.167%;
}
.gs-24 > .grid-stack-item[gs-x="13"] {
  left: 54.167%;
}
.gs-24 > .grid-stack-item[gs-w="14"] {
  width: 58.333%;
}
.gs-24 > .grid-stack-item[gs-x="14"] {
  left: 58.333%;
}
.gs-24 > .grid-stack-item[gs-w="15"] {
  width: 62.5%;
}
.gs-24 > .grid-stack-item[gs-x="15"] {
  left: 62.5%;
}
.gs-24 > .grid-stack-item[gs-w="16"] {
  width: 66.667%;
}
.gs-24 > .grid-stack-item[gs-x="16"] {
  left: 66.667%;
}
.gs-24 > .grid-stack-item[gs-w="17"] {
  width: 70.833%;
}
.gs-24 > .grid-stack-item[gs-x="17"] {
  left: 70.833%;
}
.gs-24 > .grid-stack-item[gs-w="18"] {
  width: 75%;
}
.gs-24 > .grid-stack-item[gs-x="18"] {
  left: 75%;
}
.gs-24 > .grid-stack-item[gs-w="19"] {
  width: 79.167%;
}
.gs-24 > .grid-stack-item[gs-x="19"] {
  left: 79.167%;
}
.gs-24 > .grid-stack-item[gs-w="20"] {
  width: 83.333%;
}
.gs-24 > .grid-stack-item[gs-x="20"] {
  left: 83.333%;
}
.gs-24 > .grid-stack-item[gs-w="21"] {
  width: 87.5%;
}
.gs-24 > .grid-stack-item[gs-x="21"] {
  left: 87.5%;
}
.gs-24 > .grid-stack-item[gs-w="22"] {
  width: 91.667%;
}
.gs-24 > .grid-stack-item[gs-x="22"] {
  left: 91.667%;
}
.gs-24 > .grid-stack-item[gs-w="23"] {
  width: 95.833%;
}
.gs-24 > .grid-stack-item[gs-x="23"] {
  left: 95.833%;
}
.gs-24 > .grid-stack-item[gs-w="24"] {
  width: 100%;
}
</style>