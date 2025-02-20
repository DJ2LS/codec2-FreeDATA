<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../../store/index';
setActivePinia(pinia);

import { useStateStore } from '../../store/stateStore.js';
const state = useStateStore(pinia);
</script>

<template>
  <div class="card w-100 h-100">
    <div class="card-header mb-1">
      <i class="bi bi-volume-up" style="font-size: 1rem"></i>&nbsp;
      <strong>Audio</strong>
    </div>
    <div class="card-body pt-0 pb-0">
      <div class="container-wide">
        <div class="row">
          <div class="col-lg-6">
            <div class="progress mb-0 rounded-0 rounded-top" style="height: 22px">
              <div
                class="progress-bar progress-bar-striped bg-primary force-gpu"
                id="noise_level"
                role="progressbar"
                :style="{ width: state.s_meter_strength_percent + '%' }"
                :aria-valuenow="state.s_meter_strength_percent"
                aria-valuemin="0"
                aria-valuemax="100"
              ></div>
              <p class="justify-content-center d-flex position-absolute w-100" id="noise_level_value">
                S-Meter(dB): {{ state.s_meter_strength_raw }}
              </p>
            </div>
            <div class="progress mb-0 rounded-0 rounded-bottom" style="height: 8px">
              <div class="progress-bar progress-bar-striped bg-warning" role="progressbar" style="width: 1%" aria-valuenow="1" aria-valuemin="0" aria-valuemax="100"></div>
              <div class="progress-bar bg-success" role="progressbar" style="width: 89%" aria-valuenow="50" aria-valuemin="0" aria-valuemax="100"></div>
              <div class="progress-bar progress-bar-striped bg-warning" role="progressbar" style="width: 20%" aria-valuenow="20" aria-valuemin="0" aria-valuemax="100"></div>
              <div class="progress-bar progress-bar-striped bg-danger" role="progressbar" style="width: 29%" aria-valuenow="29" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
          </div>
          <div class="col-lg-6">
            <div class="progress mb-0 rounded-0 rounded-top" style="height: 22px">
              <div
                class="progress-bar progress-bar-striped bg-primary force-gpu"
                id="dbfs_level"
                role="progressbar"
                :style="{ width: state.dbfs_level_percent + '%' }"
                :aria-valuenow="state.dbfs_level_percent"
                aria-valuemin="0"
                aria-valuemax="100"
              ></div>
              <p class="justify-content-center d-flex position-absolute w-100" id="dbfs_level_value">
                {{ state.dbfs_level }} dBFS
              </p>
            </div>
            <div class="progress mb-0 rounded-0 rounded-bottom" style="height: 8px">
              <div class="progress-bar progress-bar-striped bg-warning" role="progressbar" style="width: 1%" aria-valuenow="1" aria-valuemin="0" aria-valuemax="100"></div>
              <div class="progress-bar bg-success" role="progressbar" style="width: 89%" aria-valuenow="50" aria-valuemin="0" aria-valuemax="100"></div>
              <div class="progress-bar progress-bar-striped bg-warning" role="progressbar" style="width: 20%" aria-valuenow="20" aria-valuemin="0" aria-valuemax="100"></div>
              <div class="progress-bar progress-bar-striped bg-danger" role="progressbar" style="width: 29%" aria-valuenow="29" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Add your custom styles here, if needed */
</style>
