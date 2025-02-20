<script setup>

import { settingsStore as settings, onChange } from "../store/settingsStore.js";


// Pinia setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);


import { startModem, stopModem } from "../js/api.js";

import { useAudioStore } from "../store/audioStore";
const audioStore = useAudioStore(pinia);


function reloadModem(){
  stopModem();
  setTimeout(startModem, 5000); // Executes startModem after 5000 milliseconds as server needs to shutdown first
}

</script>

<template>
  <!-- Top Info Area for Modem and Audio Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>Modem and Audio</strong> related settings, including starting/stopping the modem, configuring audio devices, and adjusting audio levels.
  </div>

  <div class="alert alert-light" role="alert">
   Settings in <strong class="text-danger">RED</strong> require a server restart!
  </div>

  <!-- Start and Stop Modem Buttons -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Manual modem control
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Start or stop the modem. Ensure your audio and radio settings are configured first."
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <div class="w-50 d-flex justify-content-between">
      <button
        type="button"
        class="btn btn-outline-secondary btn-sm w-100 me-1"
        data-bs-toggle="tooltip"
        title="Start the Modem"
        @click="reloadModem"
      >
        <i class="bi bi-arrow-clockwise"></i>
        Reload
      </button>

    </div>
  </div>
  <!-- Modem Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap text-danger">
      Modem port
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Server restart required"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="number"
      class="form-control"
      placeholder="Enter modem port"
      id="modem_port"
      maxlength="5"
      max="65534"
      min="1025"
      @change="onChange"
      v-model.number="settings.remote.NETWORK.modemport"
    />
  </div>

  <!-- Modem Host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap text-danger">
      Modem host
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Server restart required"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="modem_host"
      @change="onChange"
      v-model="settings.remote.NETWORK.modemaddress"
    >
      <option value="127.0.0.1">127.0.0.1 (Local operation)</option>
      <option value="localhost">localhost (Local operation)</option>
      <option value="0.0.0.0">0.0.0.0 (Remote operation)</option>
    </select>
  </div>

  <!-- Audio Input Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Audio Input device
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Select your microphone or line-in device"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <select
      class="form-select form-select-sm w-50"
      @change="onChange"
      v-model="settings.remote.AUDIO.input_device"
    >
      <option v-for="device in audioStore.audioInputs" :key="device.id" :value="device.id">
        {{ device.name }} [{{ device.api }}]
      </option>
    </select>
  </div>

  <!-- Audio Output Device -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Audio Output device
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Select your speakers or output device"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <select
      class="form-select form-select-sm w-50"
      @change="onChange"
      v-model="settings.remote.AUDIO.output_device"
    >
      <option v-for="device in audioStore.audioOutputs" :key="device.id" :value="device.id">
        {{ device.name }} [{{ device.api }}]
      </option>
    </select>
  </div>

  <!-- RX Audio Level -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      RX Audio Level
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Adjust to set the receive audio gain"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <div class="input-group-text w-25">
      {{ settings.remote.AUDIO.rx_audio_level }}
    </div>
    <div class="w-25">
      <input
        type="range"
        class="form-range"
        min="-30"
        max="20"
        step="1"
        id="audioLevelRX"
        @change="onChange"
        v-model.number="settings.remote.AUDIO.rx_audio_level"
      />
    </div>
  </div>

  <!-- TX Audio Level -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      TX Audio Level
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Adjust to set the transmit audio gain"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <div class="input-group-text w-25">
      {{ settings.remote.AUDIO.tx_audio_level }}
    </div>
    <div class="w-25">
      <input
        type="range"
        class="form-range"
        min="-30"
        max="20"
        step="1"
        id="audioLevelTX"
        @change="onChange"
        v-model.number="settings.remote.AUDIO.tx_audio_level"
      />
    </div>
  </div>

  <!-- TX Delay -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      TX delay in ms
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Delay before transmitting, in milliseconds"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="tx_delay"
      @change="onChange"
      v-model.number="settings.remote.MODEM.tx_delay"
    >
      <option value="0">0</option>
      <option value="50">50</option>
      <option value="100">100</option>
      <option value="150">150</option>
      <option value="200">200</option>
      <option value="250">250</option>
      <option value="300">300</option>
      <option value="350">350</option>
      <option value="400">400</option>
      <option value="450">450</option>
      <option value="500">500</option>
      <option value="550">550</option>
      <option value="600">600</option>
      <option value="650">650</option>
      <option value="700">700</option>
      <option value="750">750</option>
      <option value="800">800</option>
      <option value="850">850</option>
      <option value="900">900</option>
      <option value="950">950</option>
      <option value="1000">1000</option>
    </select>
  </div>

  <!-- Maximum Used Bandwidth -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Maximum used bandwidth
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Select the maximum bandwidth the modem will use"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <select
      class="form-select form-select-sm w-50"
      id="maximum_bandwidth"
      @change="onChange"
      v-model.number="settings.remote.MODEM.maximum_bandwidth"
    >
      <option value="250">250 Hz</option>
      <option value="500">500 Hz</option>
      <option value="1700">1700 Hz</option>
      <option value="2438">2438 Hz</option>
    </select>
  </div>
</template>


