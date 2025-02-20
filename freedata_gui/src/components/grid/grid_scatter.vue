<script setup>
// reason for no check is, that we have some mixing of typescript and chart js which seems to be not to be fixed that easy
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
import { Scatter } from "vue-chartjs";

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
</script>

<template>

    <div class="card h-100">
    <!--325px-->
    <div class="card-header">
      <i class="bi bi-border-outer" style="font-size: 1.2rem"></i>&nbsp;
      <strong>Scatter diagram</strong>
    </div>
    <div class="card-body overflow-auto p-0">
      <Scatter :data="scatterChartData" :options="scatterChartOptions" />
    </div>
      </div>



  <!--278px-->
</template>
