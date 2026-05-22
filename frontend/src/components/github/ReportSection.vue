<script setup>
defineProps({
  section: { type: Object, required: true },
})

const iconPaths = {
  layers: 'M2 8l6 4 6-4M2 12l6 4 6-4M2 4l6 4 6-4',
  'check-circle': 'M9 1.5a7.5 7.5 0 1 1 0 15 7.5 7.5 0 0 1 0-15zM6 8.5l2 2 4-4',
  zap: 'M10 1L4 9h4l-1 6 6-8h-4l1-6z',
  shield: 'M9 1.5L2.5 4.5v4c0 3.5 3 6.5 6.5 7.5 3.5-1 6.5-4 6.5-7.5v-4L9 1.5z',
  star: 'M9 1.5l2.2 4.5 5 .7-3.6 3.5.9 5L9 12.8l-4.5 2.4.9-5L1.8 6.7l5-.7L9 1.5z',
}
</script>

<template>
  <div :id="section.id" class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6 scroll-mt-24">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5">
      <div class="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary">
          <path :d="iconPaths[section.icon] || iconPaths.layers" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        </svg>
      </div>
      <h3 class="text-lg font-bold text-ink">{{ section.title }}</h3>
    </div>

    <!-- Content -->
    <div class="report-content text-sm text-ink-light leading-relaxed" v-html="section.content"></div>
  </div>
</template>

<style>
.report-content h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-ink);
  margin: 1.25rem 0 0.5rem;
  font-family: var(--font-heading);
}
.report-content h4:first-child {
  margin-top: 0;
}
.report-content p {
  margin: 0.5rem 0;
}
.report-content ul {
  padding-left: 1.25rem;
  margin: 0.5rem 0;
}
.report-content li {
  margin-bottom: 0.25rem;
}
.report-content code {
  font-family: var(--font-mono);
  font-size: 0.8em;
  padding: 0.15em 0.4em;
  border-radius: 4px;
  background: var(--color-surface-alt);
}
.report-content strong {
  color: var(--color-ink);
  font-weight: 600;
}
</style>
