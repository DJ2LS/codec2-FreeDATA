<template>
  <div class="row justify-content-end mb-2 me-1">
    <!-- control area -->
    <div class="col-auto p-0 m-0">
      <button
        class="btn btn-outline-secondary border-0 me-1"
        @click="repeatMessage"
      >
        <i class="bi bi-arrow-repeat"></i>
      </button>

      <button
        class="btn btn-outline-secondary border-0 me-1"
        @click="showMessageInfo"
        data-bs-target="#messageInfoModal"
        data-bs-toggle="modal"
      >
        <i class="bi bi-info-circle"></i>
      </button>

      <button class="btn btn-outline-secondary border-0" @click="deleteMessage">
        <i class="bi bi-trash"></i>
      </button>

      <button class="btn btn-outline-secondary border-0" @click="sendADIF">
        ADIF
      </button>

    </div>
    <!-- message area -->
    <div :class="messageWidthClass" class="align-items-end">
      <div class="card">
        <div
          v-for="attachment in message.attachments"
          :key="attachment.id"
          class="card-header"
        >
          <chat_messages_image_preview :attachment="attachment" />
          <div class="btn-group w-100" role="group">
            <button class="btn btn-light text-truncate" disabled>
              {{ attachment.name }}
            </button>
            <button
              @click="
                downloadAttachment(attachment.hash_sha512, attachment.name)
              "
              class="btn btn-light w-25"
            >
              <i class="bi bi-download strong"></i>
            </button>
          </div>
        </div>

        <div class="card-body">
          <!-- Render parsed markdown -->
          <p class="card-text text-break" v-html="parsedMessageBody"></p>
        </div>

        <div class="card-footer p-1 border-top-0">
          <p class="text p-0 m-0 mb-1 me-1 text-end">
            <span class="badge badge-primary mr-2" :class="{
                'bg-danger': message.status == 'failed',
                'bg-primary': message.status == 'transmitting',
                'bg-secondary': message.status == 'transmitted',
              }"
            >
              {{ message.status }}
            </span>
            | <span class="badge text-bg-light mr-2"> attempt: {{ message.attempt + 1 }} </span>|<span class="badge text-bg-light mr-2"> {{ getDateTime }} UTC</span>
          </p>
        </div>

        <div
          class="card-footer p-0 border-top-0"
          v-if="message.percent < 100 || message.status === 'failed'"
        >
          <div
            class="progress rounded-0 rounded-bottom"
            hidden
            :class="{
              'bg-danger': message.status == 'failed',
              'bg-primary': message.status == 'transmitting',
              'bg-secondary': message.status == 'transmitted',
            }"
          >
            <div
              class="progress-bar progress-bar-striped overflow-visible"
              role="progressbar"
              :style="{ width: message.percent + '%', height: '10px' }"
              :aria-valuenow="message.percent"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              {{ message.percent }} % with {{ message.bytesperminute }} bpm (
              {{ message.status }} )
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from "marked";
import DOMPurify from "dompurify";
import {
  repeatMessageTransmission,
  deleteMessageFromDB,
  requestMessageInfo,
  getMessageAttachment,
  sendADIFviaUDP,
} from "../js/messagesHandler";

// pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);
import chat_messages_image_preview from './chat_messages_image_preview.vue';

import { useChatStore } from '../store/chatStore.js';
const chatStore = useChatStore(pinia);

export default {
  components: {
    chat_messages_image_preview,
  },

  props: {
    message: Object,
  },

  methods: {
    repeatMessage() {
      repeatMessageTransmission(this.message.id);
    },

    deleteMessage() {
      deleteMessageFromDB(this.message.id);
    },
    sendADIF() {
      sendADIFviaUDP(this.message.id);
    },

    showMessageInfo() {
      chatStore.messageInfoById = requestMessageInfo(this.message.id);
    },

    async downloadAttachment(hash_sha512, fileName) {
      try {
        const jsondata = await getMessageAttachment(hash_sha512);
        const byteCharacters = atob(jsondata.data);
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
          const slice = byteCharacters.slice(offset, offset + 512);
          const byteNumbers = new Array(slice.length);
          for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
          }
          const byteArray = new Uint8Array(byteNumbers);
          byteArrays.push(byteArray);
        }

        const blob = new Blob(byteArrays, { type: jsondata.type });
        const url = URL.createObjectURL(blob);

        // Creating a temporary anchor element to download the file
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = fileName;
        document.body.appendChild(anchor);
        anchor.click();

        // Cleanup
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Failed to download the attachment:", error);
      }
    },
  },

  computed: {
    messageWidthClass() {
      // Calculate a Bootstrap grid class based on message length
      if (this.message.body.length <= 50) {
        return "col-5";
      } else if (this.message.body.length <= 100) {
        return "col-6";
      } else {
        return "col-8";
      }
    },

    getDateTime() {
      let date = new Date(this.message.timestamp);
      let hours = date.getHours().toString().padStart(2, "0");
      let minutes = date.getMinutes().toString().padStart(2, "0");
      let seconds = date.getSeconds().toString().padStart(2, "0");
      return `${hours}:${minutes}:${seconds}`;
    },

    parsedMessageBody() {
     // Parse markdown to HTML
  let parsedHTML = marked.parse(this.message.body);

  // Sanitize the HTML
  let sanitizedHTML = DOMPurify.sanitize(parsedHTML);

  // Create a temporary DOM element to manipulate the sanitized output
  let tempDiv = document.createElement("div");
  tempDiv.innerHTML = sanitizedHTML;

  // Modify all links to open in a new tab
  tempDiv.querySelectorAll("a").forEach(link => {
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer"); // Security best practice
  });

  // Return the updated HTML
  return tempDiv.innerHTML;


    },
  },
};
</script>
