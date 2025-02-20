<script setup>
// reason for no check is, that we have some mixing of typescript and chart js which seems to be not to be fixed that easy
import { ref, computed, onMounted } from "vue";
import { initWaterfall } from "../../js/waterfallHandler.js";
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line, Scatter } from "vue-chartjs";

const localSpectrumView = ref("waterfall");
function selectStatsControl(item) {
  switch (item) {
    case "wf":
      localSpectrumView.value = "waterfall";
      break;
    case "scatter":
      localSpectrumView.value = "scatter";
      break;
    case "chart":
      localSpectrumView.value = "chart";
      break;
    default:
      localSpectrumView.value = "waterfall";
  }
}

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Chart.js options and data
const skipped = (speedCtx, value) =>
  speedCtx.p0.skip || speedCtx.p1.skip ? value : undefined;
const down = (speedCtx, value) =>
  speedCtx.p0.parsed.y > speedCtx.p1.parsed.y ? value : undefined;

const transmissionSpeedChartOptions = {
  responsive: true,
  animations: true,
  maintainAspectRatio: false,
  cubicInterpolationMode: "monotone",
  tension: 0.4,
  scales: {
    SNR: {
      type: "linear",
      ticks: { beginAtZero: false, color: "rgb(255, 99, 132)" },
      position: "right",
    },
    SPEED: {
      type: "linear",
      ticks: { beginAtZero: false, color: "rgb(120, 100, 120)" },
      position: "left",
      grid: {
        drawOnChartArea: false, // only want the grid lines for one axis to show up
      },
    },
    x: { ticks: { beginAtZero: true } },
  },
};

const transmissionSpeedChartData = computed(() => ({
  labels: state.arq_speed_list_timestamp,
  datasets: [
    {
      type: "line",
      label: "SNR[dB]",
      data: state.arq_speed_list_snr.value,
      borderColor: "rgb(75, 192, 192, 1.0)",
      pointRadius: 1,
      segment: {
        borderColor: (speedCtx) =>
          skipped(speedCtx, "rgb(0,0,0,0.4)") ||
          down(speedCtx, "rgb(192,75,75)"),
        borderDash: (speedCtx) => skipped(speedCtx, [3, 3]),
      },
      spanGaps: true,
      backgroundColor: "rgba(75, 192, 192, 0.2)",
      order: 1,
      yAxisID: "SNR",
    },
    {
      type: "bar",
      label: "Speed[bpm]",
      data: state.arq_speed_list_bpm.value,
      borderColor: "rgb(120, 100, 120, 1.0)",
      backgroundColor: "rgba(120, 100, 120, 0.2)",
      order: 0,
      yAxisID: "SPEED",
    },
  ],
}));

const scatterChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      type: "linear",
      position: "bottom",
      grid: {
        display: true,
        lineWidth: (context) => {
          // Make the zero line thick (3) and other grid lines thin (1)
          return context.tick.value === 0 ? 3 : 1;
        },
      },
      ticks: {
        display: false,
      },
    },
    y: {
      type: "linear",
      position: "left",
      grid: {
        display: true,
        lineWidth: (context) => {
          return context.tick.value === 0 ? 3 : 1;
        },
      },
      ticks: {
        display: false,
      },
    },
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      enabled: false,
    },
  },
};


const scatterChartData = computed(() => ({
  datasets: [
    {
      type: "scatter",
      fill: true,
      data: state.scatter,
      label: "Scatter",
      tension: 0.1,
      borderColor: "rgb(0, 255, 0)",
    },
  ],
}));

const localSpectrumID = ref("");
localSpectrumID.value =
  "gridwfid-" + (Math.random() + 1).toString(36).substring(7);

onMounted(() => {
  initWaterfall(localSpectrumID.value);
});
</script>

<template>
  <div class="card h-100">
    <div class="card-header">
      <div class="btn-group" role="group">
        <div
          class="list-group bg-body-tertiary list-group-horizontal"
          id="list-tab"
          role="tablist"
        >
          <a
            class="py-0 list-group-item list-group-item-light list-group-item-action"
            data-bs-toggle="list"
            role="tab"
            aria-controls="list-waterfall"
            :class="{ active: localSpectrumView == 'waterfall' }"
            @click="selectStatsControl('wf')"
          >
            <strong><i class="bi bi-water"></i></strong>
          </a>
          <a
            class="py-0 list-group-item list-group-item-light list-group-item-action"
            data-bs-toggle="list"
            role="tab"
            aria-controls="list-scatter"
            :class="{ active: localSpectrumView == 'scatter' }"
            @click="selectStatsControl('scatter')"
          >
            <strong><i class="bi bi-border-outer"></i></strong>
          </a>
          <a
            class="py-0 list-group-item list-group-item-light list-group-item-action"
            data-bs-toggle="list"
            role="tab"
            aria-controls="list-chart"
            :class="{ active: localSpectrumView == 'chart' }"
            @click="selectStatsControl('chart')"
          >
            <strong><i class="bi bi-graph-up-arrow"></i></strong>
          </a>
        </div>
      </div>

    </div>
    <div class="card-body w-100 h-100 overflow-auto p-2">
      <div class="tab-content h-100 w-100" id="nav-stats-tabContent">
        <div
          class="tab-pane fade h-100 w-100"
          :class="{ 'show active': localSpectrumView == 'waterfall' }"
          role="stats_tabpanel"
          aria-labelledby="list-waterfall-list"
        >
          <canvas :id="localSpectrumID" class="force-gpu"></canvas>
        </div>
        <div
          class="tab-pane fade h-100 w-100"
          :class="{ 'show active': localSpectrumView == 'scatter' }"
          role="tabpanel"
          aria-labelledby="list-scatter-list"
        >
          <Scatter :data="scatterChartData" :options="scatterChartOptions" />
        </div>
        <div
          class="tab-pane fade h-100 w-100"
          :class="{ 'show active': localSpectrumView == 'chart' }"
          role="tabpanel"
          aria-labelledby="list-chart-list"
        >
          <Line
            :data="transmissionSpeedChartData"
            :options="transmissionSpeedChartOptions"
          />
        </div>
      </div>
    </div>

    <div class=card-footer p-1>

    <div class="btn-group" role="group" aria-label="Busy indicators">
        <button
          class="btn btn-sm ms-1 p-1 disabled"
          type="button"
          data-bs-placement="top"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="true"
          :class="{
            'btn-warning': state.channel_busy_slot[0] === true,
            'btn-outline-secondary': state.channel_busy_slot[0] === false,
          }"
          title="Channel busy state: <strong class='text-success'>not busy</strong> / <strong class='text-danger'>busy </strong>"
        >
          S1
        </button>

        <button
          class="btn btn-sm p-1 disabled"
          type="button"
          data-bs-placement="top"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="true"
          :class="{
            'btn-warning': state.channel_busy_slot[1] === true,
            'btn-outline-secondary': state.channel_busy_slot[1] === false,
          }"
          title="Channel busy state: <strong class='text-success'>not busy</strong> / <strong class='text-danger'>busy </strong>"
        >
          S2
        </button>

        <button
          class="btn btn-sm p-1 disabled"
          type="button"
          data-bs-placement="top"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="true"
          :class="{
            'btn-warning': state.channel_busy_slot[2] === true,
            'btn-outline-secondary': state.channel_busy_slot[2] === false,
          }"
          title="Channel busy state: <strong class='text-success'>not busy</strong> / <strong class='text-danger'>busy </strong>"
        >
          S3
        </button>

        <button
          class="btn btn-sm p-1 disabled"
          type="button"
          data-bs-placement="top"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="true"
          :class="{
            'btn-warning': state.channel_busy_slot[3] === true,
            'btn-outline-secondary': state.channel_busy_slot[3] === false,
          }"
          title="Channel busy state: <strong class='text-success'>not busy</strong> / <strong class='text-danger'>busy </strong>"
        >
          S4
        </button>

        <button
          class="btn btn-sm p-1 disabled"
          type="button"
          data-bs-placement="top"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="true"
          :class="{
            'btn-warning': state.channel_busy_slot[4] === true,
            'btn-outline-secondary': state.channel_busy_slot[4] === false,
          }"
          title="Channel busy state: <strong class='text-success'>not busy</strong> / <strong class='text-danger'>busy </strong>"
        >
          S5
        </button>

        <button
          class="btn btn-sm p-1 disabled"
          type="button"
          data-bs-placement="top"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="true"
          title="Receiving data: illuminates <strong class='text-success'>green</strong> if receiving codec2 data"
          :class="{
            'btn-success': state.is_codec2_traffic === true,
            'btn-outline-secondary': state.is_codec2_traffic === false,
          }"
        >
          data
        </button>
      </div>
    </div>




  </div>
</template>
