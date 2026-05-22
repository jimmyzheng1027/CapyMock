<script setup>
import { computed } from 'vue'

const props = defineProps({
  repo: { type: Object, required: true },
})

const avatarColor = computed(() => {
  const colors = ['#B8845C', '#7A9E6F', '#E07858', '#6B8EC4', '#9B7EC4']
  let hash = 0
  for (const ch of props.repo.owner) hash = ch.charCodeAt(0) + ((hash << 5) - hash)
  return colors[Math.abs(hash) % colors.length]
})

const relativeTime = computed(() => {
  const now = Date.now()
  const then = new Date(props.repo.analyzedAt).getTime()
  const diff = now - then
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (days > 0) return `${days} 天前`
  if (hours > 0) return `${hours} 小时前`
  if (minutes > 0) return `${minutes} 分钟前`
  return '刚刚'
})

const visibleTags = computed(() => props.repo.techTags?.slice(0, 4) || [])
</script>

<template>
  <router-link
    :to="`/analysis/github/${repo.id}`"
    class="block bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-5 transition-all hover:shadow-md hover:border-primary/40 cursor-pointer no-underline"
  >
    <div class="flex items-start gap-4">
      <!-- Avatar -->
      <div
        class="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
        :style="{ background: avatarColor }"
      >
        {{ repo.owner.charAt(0).toUpperCase() }}
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-ink truncate">{{ repo.fullName }}</h3>
          <div
            class="shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white"
            :style="{
              background: repo.score >= 80 ? 'var(--color-secondary)' : repo.score >= 60 ? 'var(--color-primary)' : 'var(--color-accent)',
            }"
          >
            {{ repo.score }}
          </div>
        </div>

        <p class="text-xs text-ink-muted mt-1 line-clamp-2 leading-relaxed">{{ repo.description }}</p>

        <!-- Tags -->
        <div class="flex flex-wrap gap-1.5 mt-3">
          <span
            v-for="tag in visibleTags"
            :key="tag"
            class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary-dark"
          >
            {{ tag }}
          </span>
        </div>

        <!-- Time -->
        <div class="mt-3 text-[11px] text-ink-muted">{{ relativeTime }}</div>
      </div>
    </div>
  </router-link>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
