<template>
  <div class="row justify-content-start mb-2">
    <div :class="messageWidthClass">
      <div class="card bg-light border rounded-top text-dark">
        <div
          v-for="attachment in message.attachments"
          :key="attachment.id"
          class="card-header"
        >

          <chat_messages_image_preview :attachment="attachment" />

          <div class="btn-group w-100" role="group">
            <button class="btn btn-light border rounded-bottom text-truncate" disabled>
              {{ attachment.name }}
            </button>
            <button
              @click="
                downloadAttachment(attachment.hash_sha512, attachment.name)
              "
              class="btn btn-light border rounded-bottom w-25"
            >
              <i class="bi bi-download strong"></i>
            </button>
          </div>
        </div>

        <div class="card-body">
          <!-- Render parsed markdown with v-html -->
          <p class="card-text text-break" v-html="parsedMessageBody"></p>
        </div>

        <div class="card-footer p-0 border-top-0">
          <p class="p-0 m-0 me-1 text-end text-dark">
            <span class="badge badge-secondary mr-2 text-dark">{{ getDateTime }} UTC</span>
          </p>
          <!-- Display formatted timestamp in card-footer -->
        </div>
      </div>
    </div>

    <!-- Delete button outside of the card -->
    <div class="col-auto">
      <button
        class="btn btn-outline-secondary border-0 me-1"
        @click="showMessageInfo"
        data-bs-target="#messageInfoModal"
        data-bs-toggle="modal"
      >
        <i class="bi bi-info-circle"></i>
      </button>

      <button class="btn btn-outline-secondary border-0" @click="sendADIF">
        ADIF
      </button>

      <button class="btn btn-outline-secondary border-0" @click="deleteMessage">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  </div>
</template>

<script>
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import {
  deleteMessageFromDB,
  requestMessageInfo,
  getMessageAttachment, sendADIFviaUDP,
} from "../js/messagesHandler";

import chat_messages_image_preview from './chat_messages_image_preview.vue';

// Pinia store setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

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
    showMessageInfo() {
      chatStore.messageInfoById = requestMessageInfo(this.message.id);
    },

    sendADIF() {
      sendADIFviaUDP(this.message.id);
    },

    deleteMessage() {
      deleteMessageFromDB(this.message.id);
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
        return "col-4";
      } else if (this.message.body.length <= 100) {
        return "col-6";
      } else {
        return "col-9";
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
