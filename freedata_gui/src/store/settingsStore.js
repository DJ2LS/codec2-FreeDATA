import { reactive, watch } from "vue";
import { getConfig, setConfig } from "../js/api";

// Default configuration
const defaultConfig = {
  local: {
    host: "127.0.0.1",
    port: "5000",
    spectrum: "waterfall",
    wf_theme: 2,
    enable_sys_notification: false,
    grid_layout: "[]",
    grid_preset: "[]",
    grid_enabled: true,
  },
  remote: {
    AUDIO: {
      enable_auto_tune: false,
      input_device: "",
      output_device: "",
      rx_audio_level: 0,
      tx_audio_level: 0,
    },
    MODEM: {
      tx_delay: 0,
      enable_morse_identifier: false,
      maximum_bandwidth: 3000,
    },
    NETWORK: {
            modemaddress: "127.0.0.1",
            modemport: 5000,
        },
    RADIO: {
      control: "disabled",
      model_id: 0,
      serial_port: "",
      serial_speed: "",
      data_bits: 0,
      stop_bits: 0,
      serial_handshake: "",
      ptt_port: "",
      ptt_type: "",
      serial_dcd: "",
      serial_dtr: "",
      serial_rts: "",
    },
    RIGCTLD: {
      ip: "127.0.0.1",
      port: 0,
      path: "",
      command: "",
      arguments: "",
      enable_vfo: false,
    },
    STATION: {
      enable_explorer: false,
      enable_stats: false,
      mycall: "DEFAULT",
      myssid: 0,
      mygrid: "",
      ssid_list: [],
      respond_to_cq: false,
      enable_callsign_blacklist: false,
      callsign_blacklist: [],
    },
    TCI: {
      tci_ip: "127.0.0.1",
      tci_port: 0,
    },
    MESSAGES: {
      enable_auto_repeat: false,
    },
    SOCKET_INTERFACE: {
      enable: false,
      host: "127.0.0.1",
      cmd_port: 8000,
      data_port: 8001,
    },

    QSO_LOGGING: {
      enable_adif_udp: false,
      adif_udp_host: "127.0.0.1",
      adif_udp_port: "2237",
      enable_adif_wavelog: false,
      adif_wavelog_host: "127.0.0.1",
      adif_wavelog_api_key: "",
    },

    GUI: {
      auto_run_browser: true,
    },
  },
};

// Initialize local settings from browser storage
const localConfig =
  JSON.parse(localStorage.getItem("localConfig")) || defaultConfig.local;
console.log("--------- LOCAL CONFIG -----------");
console.log(localConfig);

export const settingsStore = reactive({ ...defaultConfig, local: localConfig });
// Function to handle remote configuration changes

export function onChange() {
  let remote_config = settingsStore.remote;
  let blacklistContent = remote_config.STATION.callsign_blacklist;
  // Check if the content is a string
  if (typeof blacklistContent === "string") {
    // Split the string by newlines to create an array
    blacklistContent = blacklistContent
      .split("\n") // Split text by newlines
      .map((item) => item.trim()) // Trim whitespace from each line
      .filter((item) => item !== ""); // Remove empty lines

    // Update the settings store with the validated array
    remote_config.STATION.callsign_blacklist = blacklistContent;
  }

  // Ensure it's an array, even if the data comes in incorrectly formatted
  if (!Array.isArray(blacklistContent)) {
    // Convert any other data types to an empty array as a fallback
    remote_config.STATION.callsign_blacklist = [];
  }

  setConfig(remote_config).then((conf) => {
    settingsStore.remote = conf;
    settingsStore.remote.STATION.callsign_blacklist =
      conf.STATION.callsign_blacklist.join("\n");
  });
}

// Function to fetch remote configuration
export function getRemote() {
  return getConfig().then((conf) => {
    if (conf !== undefined) {
      settingsStore.remote = conf;
      settingsStore.remote.STATION.callsign_blacklist =
        conf.STATION.callsign_blacklist.join("\n");
      onChange();
    } else {
      console.warn("Received undefined configuration, using default!");
      settingsStore.remote = defaultConfig.remote;
    }
  });
}

// Watcher to save local settings on change
watch(
  () => settingsStore.local,
  () => {
    saveLocalSettingsToConfig();
  },
  { deep: true },
);

// Function to save local settings to browser storage
export function saveLocalSettingsToConfig() {
  localStorage.setItem("localConfig", JSON.stringify(settingsStore.local));
  console.log("Settings saved!");
}
