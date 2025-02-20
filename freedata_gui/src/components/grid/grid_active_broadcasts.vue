<script setup>
import { ref } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
import { useStateStore } from "../../store/stateStore.js";
import { sendModemCQ, sendModemPing, setModemBeacon } from "../../js/api.js";

// Set the active Pinia store
setActivePinia(pinia);
const state = useStateStore(pinia);

// Reactive reference for DX Call
const dxcallPing = ref("");

// Reactive references to manage button states
const isCQButtonDisabled = ref(false);
const isPingButtonDisabled = ref(false);



// Function to transmit a ping
async function transmitPing() {
  isPingButtonDisabled.value = true;

  // Send Ping message
  await sendModemPing(dxcallPing.value.toUpperCase());

  // Wait for 6 seconds (cooldown period)
  setTimeout(() => {
    isPingButtonDisabled.value = false;
  }, 6000);
}

// Function to send CQ and handle button disable and cooldown
async function handleSendCQ() {
  isCQButtonDisabled.value = true;

  // Send CQ message
  await sendModemCQ();

  // Wait for 6 seconds (cooldown period)
  setTimeout(() => {
    isCQButtonDisabled.value = false;
  }, 10000);
}


// Function to start or stop the beacon
function startStopBeacon() {
  if (state.beacon_state) {
    setModemBeacon(false);
  } else {
    setModemBeacon(true);
  }
}

// Listen for the stationSelected event and update dxcallPing
window.addEventListener(
  "stationSelected",
  function (eventdata) {
    const evt = eventdata;
    dxcallPing.value = evt.detail;
  },
  false
);
</script>

<template>
  <div class="card h-100">
    <div class="card-header">
      <i class="bi bi-broadcast" style="font-size: 1.2rem"></i>&nbsp;
      <strong>Broadcasts</strong>
    </div>
    <div class="card-body overflow-auto">
      <div class="input-group">
        <input
          type="text"
          class="form-control"
          style="max-width: 6rem; min-width: 3rem; text-transform: uppercase"
          placeholder="DXcall"
          pattern="[A-Z]*"
          maxlength="11"
          aria-label="Input group"
          aria-describedby="btnGroupAddon"
          v-model="dxcallPing"
        />
        <button
          class="btn btn-outline-secondary"
          id="sendPing"
          type="button"
          data-bs-placement="bottom"
          data-bs-toggle="tooltip"
          data-bs-trigger="hover"
          data-bs-html="false"
          title="Send a ping request to a remote station"
          @click="transmitPing"
        >
                          <strong v-if="!isPingButtonDisabled">PING Station</strong>
                <strong v-else>Sending...</strong>
        </button>

        <button
          class="btn btn-outline-secondary ms-1"
          id="sendCQ"
          type="button"
          title="Send a CQ to the world"
          @click="handleSendCQ"
        >
          <span v-if="!isCQButtonDisabled">Call CQ</span>
                <span v-else>Sending CQ...</span>
        </button>

        <button
          type="button"
          id="startBeacon"
          class="btn ms-1"
          @click="startStopBeacon"
          :class="{
            'btn-success': state.beacon_state,
            'btn-outline-secondary': !state.beacon_state,
          }"
          title="Toggle beacon mode. The interval can be set in settings. While sending a beacon, you can receive ping requests and open a datachannel. If a datachannel is opened, the beacon pauses."
        >
          Toggle beacon
        </button>
      </div>
      <!-- end of row-->
    </div>
  </div>
</template>
