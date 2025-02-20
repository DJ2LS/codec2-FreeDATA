<template>
  <div v-if="isImage">
    <img :src="imageUrl" alt="Image Preview" class="img-fluid border rounded-top bg-light w-100" />
  </div>
</template>

<script setup>
import { computed, toRefs } from 'vue';

// eslint-disable-next-line
const props = defineProps(['attachment'])
const { attachment } = toRefs(props);

const isImage = computed(() => {
  const imageFormats = ["gif", "png", "jpg", "jpeg", "svg"];
  const extension = attachment.value.name.split(".").pop().toLowerCase();
  return imageFormats.includes(extension);
});

const imageUrl = computed(() => {
  return isImage.value ? `data:${attachment.value.type};base64,${attachment.value.data}` : "";
});
</script>

