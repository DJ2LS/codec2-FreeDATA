<script setup>

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

</script>

<template>
  <!-- Top Warning Area -->
  <div class="alert alert-danger" role="alert">
    <strong><i class="bi bi-shield-exclamation me-1"></i>WARNING:</strong> These features may be incomplete. They are for <u>experienced</u> users ONLY!
  </div>


  <div class="alert alert-info" role="alert">
    <strong><i class="bi bi-info-circle me-1"></i>Info:</strong> No features published for testing, yet.
  </div>


</template>

