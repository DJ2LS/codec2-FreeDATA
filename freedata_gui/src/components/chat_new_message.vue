<script setup>
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);

import { newMessage } from '../js/messagesHandler.js';
import { ref } from 'vue';
import { VuemojiPicker } from 'vuemoji-picker';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import ImageCompressor from 'js-image-compressor'; // Import the compressor
import { displayToast } from "../js/popupHandler";



// Emoji Handling
const handleEmojiClick = (detail) => {
  chat.inputText += detail.unicode;
};

// References for DOM elements
const chatModuleMessage = ref(null);
const fileInput = ref(null);
const selectedFiles = ref([]);

// Function to trigger the hidden file input
function triggerFileInput() {
  fileInput.value.click();
}

// Handle file selection and preview
function handleFileSelection(event) {
  handleFiles(event.target.files);
}

// Handle drag and drop files
function handleDrop(event) {
  event.preventDefault();
  event.stopPropagation();
  handleFiles(event.dataTransfer.files);
}

// Handle files from file input or drag-and-drop
// Handle files from file input or drag-and-drop
function handleFiles(files) {
  for (let file of files) {
    if (file.type.startsWith('image/')) {
      // Compress the image if it's an image type
      const options = {
        file: file,
        quality: 0.5,
        //mimeType: 'image/jpeg',
        maxWidth: 750,  // Set maximum width to 750px
        maxHeight: 750, // Set maximum height to 750px
        convertSize: Infinity,
        loose: true,
        redressOrientation: true,

        // Callback before compression
        beforeCompress: function (result) {
          console.log('Image size before compression:', result.size);
          console.log('mime type:', result.type);
        },

        // Compression success callback
        success: function (compressedFile) {
          console.log('Image size after compression:', compressedFile.size);
          console.log('mime type:', compressedFile.type);
          console.log(
            'Actual compression ratio:',
            ((file.size - compressedFile.size) / file.size * 100).toFixed(2) + '%'
          );

          // Check if compression made the file larger
          if (compressedFile.size >= file.size) {
            console.warn("Compressed file is larger than original. Using original file instead.");
            compressedFile = file; // Use original file
          }
          // toast notification
          let message = `
              <div>
                <strong> Prepared <span class="badge bg-secondary"> ${file.name}</span></strong>
                <div class="mt-2">
                  <span class="badge bg-secondary"> ${file.size} Bytes</span>
                  <i class="bi bi-caret-right-fill"></i>
                  <span class="badge bg-secondary"> ${compressedFile.size} Bytes</span>
                  <span class="badge bg-warning text-dark">Ratio:${((file.size - compressedFile.size) / file.size * 100).toFixed(2)}%.</span>
                </div>
              </div>
            `;
          displayToast(
            "success",
            "bi-card-image",
            message,
            10000
          );

          // Convert compressed image to base64
          const reader = new FileReader();
          reader.onload = () => {
            const base64Content = btoa(reader.result);
            selectedFiles.value.push({
              name: compressedFile.name,
              size: compressedFile.size,
              type: compressedFile.type,
              content: base64Content,
            });
          };
          reader.readAsBinaryString(compressedFile);
        },

        // An error occurred
        error: function (msg) {
          console.error(msg);
          displayToast(
            "danger",
            "bi-card-image",
            `Error compressing image`,
            5000
          );
        },
      };

      // Run image compression
      new ImageCompressor(options);
    } else {
      // Handle non-image files
      const reader = new FileReader();
      reader.onload = () => {
        const base64Content = btoa(reader.result);
        selectedFiles.value.push({
          name: file.name,
          size: file.size,
          type: file.type,
          content: base64Content,
        });
      };
      reader.readAsBinaryString(file);
    }
  }
}

// Remove a file from the selected list
function removeFile(index) {
  selectedFiles.value.splice(index, 1);
  if (selectedFiles.value.length === 0) {
    resetFile();
  }
}

// Transmit a new message
function transmitNewMessage() {
  if (typeof chat.selectedCallsign === 'undefined') {
    chat.selectedCallsign = Object.keys(chat.callsign_list)[0];
  }

  chat.inputText = chat.inputText.trim();
  if (chat.inputText.length === 0 && selectedFiles.value.length === 0) return;

  const attachments = selectedFiles.value.map((file) => ({
    name: file.name,
    type: file.type,
    data: file.content,
  }));

  // Sanitize inputText before sending the message
  const sanitizedInput = DOMPurify.sanitize(marked.parse(chat.inputText));

  if (chat.selectedCallsign.startsWith('BC-')) {
    return 'new broadcast';
  } else {
    if (attachments.length > 0) {
      newMessage(chat.selectedCallsign, sanitizedInput, attachments);
    } else {
      newMessage(chat.selectedCallsign, sanitizedInput);
    }
  }

  chat.inputText = '';
  chatModuleMessage.value = '';
  resetFile();
}

// Reset the file input and selected files
function resetFile() {
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  selectedFiles.value = [];
}

// Apply Markdown Formatting
function applyMarkdown(formatType) {
  const textarea = chatModuleMessage.value;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selectedText = chat.inputText.substring(start, end);

  if (formatType === 'bold') {
    chat.inputText = chat.inputText.substring(0, start) + `**${selectedText}**` + chat.inputText.substring(end);
  } else if (formatType === 'italic') {
    chat.inputText = chat.inputText.substring(0, start) + `_${selectedText}_` + chat.inputText.substring(end);
  } else if (formatType === 'underline') {
    chat.inputText = chat.inputText.substring(0, start) + `<u>${selectedText}</u>` + chat.inputText.substring(end);
  }
}
</script>

<template>
  <nav class="navbar sticky-bottom bg-body-tertiary border-top" @dragover.prevent @drop="handleDrop">
    <div class="container-fluid p-0">
      <!-- Hidden file input -->
      <input type="file" multiple ref="fileInput" @change="handleFileSelection" style="display: none;" />

      <!-- File Attachment Preview Area -->
      <div class="container-fluid">
        <div class="d-flex flex-row overflow-auto bg-light">
          <div v-for="(file, index) in selectedFiles" :key="index" class="p-2">
            <div class="card" style="min-width: 10rem; max-width: 10rem;">
              <!-- Card Header with Remove Button -->
              <div class="card-header d-flex justify-content-between align-items-center">
                <span class="text-truncate">{{ file.name }}</span>
                <button class="btn btn-close" @click="removeFile(index)"></button>
              </div>

              <!-- Conditional Image Preview -->
        <div v-if="file.type.startsWith('image/')" class="p-2">
          <img
  :src="`data:${file.type};base64,${file.content}`"
  class="img-fluid"
  alt="Image Preview">



        </div>

              <div class="card-footer text-muted">
                {{ file.type }}
              </div>
              <div class="card-footer text-muted">
                {{ file.size }} bytes
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Message Input Area -->
      <div class="input-group bottom-0 ms-2">
        <button
          type="button"
          class="btn btn-outline-secondary border-0 rounded-pill me-1"
          data-bs-toggle="modal"
          data-bs-target="#emojiPickerModal"
          data-bs-backdrop="false"
          @click="$refs.chatModuleMessage.focus()"
        >
          <i id="emojipickerbutton" class="bi bi-emoji-smile p-0" style="font-size: 1rem"></i>
        </button>

        <!-- Trigger file selection modal -->
        <button
          type="button"
          class="btn btn-outline-secondary border-0 rounded-pill me-1"
          @click="triggerFileInput(), $event.target.blur(), $refs.chatModuleMessage.focus()"
        >
          <i class="bi bi-paperclip" style="font-size: 1.2rem"></i>
        </button>

        <div class="vr mx-2"></div>

        <!-- Markdown Formatting Buttons -->
        <button class="btn btn-outline-secondary border-0 rounded-pill" @click="applyMarkdown('bold')"><b>B</b></button>
        <button class="btn btn-outline-secondary border-0 rounded-pill" @click="applyMarkdown('italic')"><i>I</i></button>
        <button class="btn btn-outline-secondary border-0 rounded-pill" @click="applyMarkdown('underline')"><u>U</u></button>

        <textarea
          class="form-control border rounded-pill"
          rows="1"
          ref="chatModuleMessage"
          placeholder="Message - Send with [Enter]"
          v-model="chat.inputText"
          @keyup.enter="transmitNewMessage()"
          style="resize: none;"
        ></textarea>

        <button
          class="btn btn-sm btn-secondary ms-1 me-2 rounded-pill"
          @click="transmitNewMessage()"
          type="button"
        >
          <i class="bi bi-send ms-4 me-4" style="font-size: 1.2rem"></i>
        </button>
      </div>
    </div>
  </nav>

  <!-- Emoji Picker Modal -->
  <div class="modal fade" id="emojiPickerModal" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal">
      <div class="modal-content">
        <div class="modal-header">
        <h5 class="modal-title">Insert emoji</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" data-bs-target="#emojiPickerModal" aria-label="Close"></button>
      </div>

        <div class="modal-body">
          <VuemojiPicker @emojiClick="handleEmojiClick"/>
        </div>
      </div>
    </div>
  </div>
</template>
