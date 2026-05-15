<script setup>
import { useScrollReveal } from '@/composables/useScrollReveal.js'
import NavSection from '@/components/landing/NavSection.vue'
import HeroSection from '@/components/landing/HeroSection.vue'
import FeaturesSection from '@/components/landing/FeaturesSection.vue'
import InterviewSection from '@/components/landing/InterviewSection.vue'
import CtaSection from '@/components/landing/CtaSection.vue'
import FooterSection from '@/components/landing/FooterSection.vue'
import TweaksPanel from '@/components/landing/TweaksPanel.vue'

useScrollReveal()
</script>

<template>
  <div class="min-h-screen bg-base dark:bg-base transition-theme">
    <NavSection />
    <HeroSection />
    <FeaturesSection />
    <InterviewSection />
    <CtaSection />
    <FooterSection />
    <TweaksPanel />
  </div>
</template>
