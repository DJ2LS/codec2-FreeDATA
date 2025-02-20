<script setup>
import { computed } from "vue";
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
import { Line } from "vue-chartjs";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

// https://www.chartjs.org/docs/latest/samples/line/segments.html
const skipped = (speedCtx, value) =>
  speedCtx.p0.skip || speedCtx.p1.skip ? value : undefined;
const down = (speedCtx, value) =>
  speedCtx.p0.parsed.y > speedCtx.p1.parsed.y ? value : undefined;

var transmissionSpeedChartOptions = {
  //type: "line",
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
      data: state.arq_speed_list_snr,
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
      data: state.arq_speed_list_bpm,
      borderColor: "rgb(120, 100, 120, 1.0)",
      backgroundColor: "rgba(120, 100, 120, 0.2)",
      order: 0,
      yAxisID: "SPEED",
    },
  ],
}));
</script>

<template>
   <div class="card h-100">
    <!--325px-->
    <div class="card-header">
      <i class="bi bi-graph-up-arrow" style="font-size: 1.2rem"></i>&nbsp;
      <strong>Transmission Charts</strong>
    </div>
    <div class="card-body overflow-auto p-0">
  <Line
    :data="transmissionSpeedChartData"
    :options="transmissionSpeedChartOptions"
  />
        </div>
       </div>
</template>
