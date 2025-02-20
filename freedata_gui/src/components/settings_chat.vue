<script>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { setActivePinia } from "pinia";
import pinia from "../store/index";

// Set the active Pinia store
setActivePinia(pinia);

// Export methods and computed properties for use in the template
export default {
  methods: {
    onChange,
  },
  computed: {
    settings() {
      return settings;
    },
  },
};
</script>

<template>
  <!-- Top Info Area for Messages Settings -->
  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-gear-wide-connected me-1"></i>Messages</strong> related settings, like enabling <strong>message auto repeat</strong> and configuring <strong>ADIF log</strong> connection.
  </div>

  <!-- Enable Message Auto Repeat -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Enable message auto repeat
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Re-send message on beacon"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableMessagesAutoRepeatSwitch"
          @change="onChange"
          v-model="settings.remote.MESSAGES.enable_auto_repeat"
        />
        <label class="form-check-label" for="enableMessagesAutoRepeatSwitch">Enable</label>
      </div>
    </label>
  </div>

<!-- Enable ADIF export -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Enable ADIF
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enable ADIF via UDP"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableADIFSwitch"
          @change="onChange"
          v-model="settings.remote.QSO_LOGGING.enable_adif_udp"
        />
        <label class="form-check-label" for="enableADIFSwitch">Enable</label>
      </div>
    </label>
  </div>

  <!-- ADIF Log Host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      ADIF Log Host
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="ADIF server host, e.g., 127.0.0.1"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter ADIF server host"
      id="adifLogHost"
      @change="onChange"
      v-model="settings.remote.QSO_LOGGING.adif_udp_host"
    />
  </div>

  <!-- ADIF Log Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      ADIF Log Port
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="ADIF server port, e.g., 2237"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="number"
      class="form-control"
      placeholder="Enter ADIF server port"
      id="adifLogPort"
      max="65534"
      min="1025"
      @change="onChange"
      v-model.number="settings.remote.QSO_LOGGING.adif_udp_port"
    />
  </div>

<!-- Enable Wavelog API -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Enable Wavelog API
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Enable Wavelog API"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline ms-2">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableWavelogSwitch"
          @change="onChange"
          v-model="settings.remote.QSO_LOGGING.enable_adif_wavelog"
        />
        <label class="form-check-label" for="enableWavelogSwitch">Enable</label>
      </div>
    </label>
  </div>

  <!-- Wavelog Host -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Wavelog API Host
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Wavelog API server host, e.g., 127.0.0.1"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter wavelog server host"
      id="wavelogHost"
      @change="onChange"
      v-model="settings.remote.QSO_LOGGING.adif_wavelog_host"
    />
  </div>
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      Wavelog API key
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        title="Wavelog API key"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="text"
      class="form-control"
      placeholder="Enter Wavelog api key"
      id="wavelogApiKey"
      @change="onChange"
      v-model="settings.remote.QSO_LOGGING.adif_wavelog_api_key"
    />
  </div>
</template>

