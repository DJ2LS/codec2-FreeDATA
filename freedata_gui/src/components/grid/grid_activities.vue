<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);

import { useStateStore } from '../../store/stateStore.js';
const state = useStateStore(pinia);

function getDateTime(timestampRaw) {
  var datetime = new Date(timestampRaw * 1000).toLocaleString(
    navigator.language,
    {
      hourCycle: 'h23',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }
  );
  return datetime;
}
</script>

<template>
  <div class="card h-100">
    <div class="card-header">
      <i class="bi bi-card-list" style="font-size: 1.2rem"></i>&nbsp;
      <strong>Activity</strong>
    </div>
    <div class="card-body overflow-auto m-0" style="align-items: start">
      <div v-for="item in state.activities" :key="item[0]">
        <h6 style="text-align: start" class="mb-0">
        <span class="badge text-bg-primary">{{ item[1].origin }}</span>
          -
          <span class="badge text-bg-secondary">{{getDateTime(item[1].timestamp) }}</span>


        </h6>

        <p class="mb-2" style="text-align: start; font-size: smaller">
          <small>{{ item[1].activity_type }} - {{ item[1].direction }}</small>
        </p>
      </div>
    </div>
  </div>
</template>
