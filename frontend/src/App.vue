<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

watch(
  () => route.path,
  () => {
    window.scrollTo({ top: 0 })
  }
)
</script>

<template>
  <router-view />
</template>
