<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  depth: { type: Number, default: 0 },
})

const expanded = ref(props.node.expanded ?? props.depth < 2)

const isFolder = computed(() => props.node.type === 'folder')
const indent = computed(() => `${props.depth * 20}px`)

const fileColor = computed(() => {
  const lang = props.node.language
  const map = {
    tsx: '#61DAFB',
    jsx: '#61DAFB',
    ts: '#3178C6',
    js: '#F7DF1E',
    vue: '#42B883',
    css: '#A855F7',
    scss: '#A855F7',
    json: '#EAB308',
    md: '#8A847B',
    html: '#E34F26',
    rs: '#DEA584',
    toml: '#8A847B',
  }
  return map[lang] || 'var(--color-ink-muted)'
})

function toggle() {
  if (isFolder.value) expanded.value = !expanded.value
}
</script>

<template>
  <div>
    <!-- Node row -->
    <div
      class="flex items-center gap-2 py-1 px-2 rounded-md cursor-pointer hover:bg-surface-alt transition-colors text-sm font-mono"
      :style="{ paddingLeft: indent }"
      @click="toggle"
    >
      <!-- Chevron for folders -->
      <svg
        v-if="isFolder"
        width="14" height="14" viewBox="0 0 14 14" fill="none"
        class="shrink-0 transition-transform duration-200"
        :class="expanded ? 'rotate-90' : ''"
        style="color: var(--color-ink-muted)"
      >
        <path d="M5 3l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span v-else class="w-3.5 shrink-0"></span>

      <!-- Folder icon -->
      <svg v-if="isFolder" width="16" height="16" viewBox="0 0 16 16" fill="none" class="shrink-0" style="color: var(--color-primary)">
        <path d="M2 4c0-.6.4-1 1-1h3.2l1.8 2h5c.6 0 1 .4 1 1v6c0 .6-.4 1-1 1H3c-.6 0-1-.4-1-1V4z" fill="currentColor" opacity="0.2"/>
        <path d="M2 4c0-.6.4-1 1-1h3.2l1.8 2h5c.6 0 1 .4 1 1v6c0 .6-.4 1-1 1H3c-.6 0-1-.4-1-1V4z" stroke="currentColor" stroke-width="1.2"/>
      </svg>

      <!-- File icon -->
      <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none" class="shrink-0">
        <path d="M4 2h5l4 4v7c0 .6-.4 1-1 1H4c-.6 0-1-.4-1-1V3c0-.6.4-1 1-1z" :stroke="fileColor" stroke-width="1.2" fill="none"/>
        <path d="M9 2v4h4" :stroke="fileColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>

      <!-- Name -->
      <span :class="isFolder ? 'font-medium text-ink' : 'text-ink-light'">{{ node.name }}</span>
    </div>

    <!-- Children -->
    <Transition name="tree-expand">
      <div v-if="isFolder && expanded && node.children">
        <DirectoryTree
          v-for="child in node.children"
          :key="child.name"
          :node="child"
          :depth="depth + 1"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.tree-expand-enter-active,
.tree-expand-leave-active {
  transition: opacity 0.15s ease;
  overflow: hidden;
}
.tree-expand-enter-from,
.tree-expand-leave-to {
  opacity: 0;
}
</style>
