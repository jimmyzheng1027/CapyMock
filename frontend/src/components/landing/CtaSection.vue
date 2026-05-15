<template>
  <section :style="{ padding: '5rem 0' }">
    <div class="container text-center">
      <div class="reveal">
        <!-- Happy capybara -->
        <svg width="120" height="100" viewBox="0 0 120 100" fill="none" class="mx-auto mb-8">
          <path d="M60 80 C25 80, 8 60, 12 40 C15 25, 30 12, 60 10 C90 12, 105 25, 108 40 C112 60, 95 80, 60 80 Z" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <path d="M35 16 C32 6, 42 3, 44 12" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" fill="none"/>
          <path d="M76 12 C74 2, 84 0, 85 10" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" fill="none"/>
          <path d="M40 38 Q44 34 48 38" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <path d="M68 35 Q72 31 76 35" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <path d="M58 46 L58 56" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round"/>
          <path d="M48 56 Q58 70 68 56" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <ellipse cx="58" cy="62" rx="6" ry="5" fill="#E8937A" opacity="0.5"/>
          <path d="M18 50 C8 42, 2 32, 8 25" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <path d="M102 50 C112 42, 118 32, 112 25" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <path d="M38 78 C32 88, 28 95, 25 98" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <path d="M82 78 C88 88, 92 95, 95 98" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
        </svg>

        <h2 class="text-3xl lg:text-5xl font-bold mb-4" style="font-family: var(--font-heading)">准备好了吗？</h2>
        <p class="text-lg mb-8 mx-auto" style="color: var(--color-ink-light); max-width: 560px; line-height: var(--leading-relaxed)">
          无论你是应届生还是想跳槽的职场人，CapyMock 都能帮你更自信地面对下一场面试
        </p>
        <router-link
          to="/interview"
          class="btn btn--primary no-underline inline-flex"
          style="font-size: var(--text-lg); padding: 1rem 2.5rem"
        >
          立即开始，免费使用
        </router-link>
      </div>
    </div>
  </section>
</template>
