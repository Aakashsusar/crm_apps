<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold text-gray-900 mb-6">Call Center Test Page</h1>
      
      <!-- Simple test component -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-xl font-semibold mb-4">Test Component</h2>
        <p class="text-gray-600">This is a test to verify the components are loading properly.</p>
        
        <!-- Test some basic functionality -->
        <div class="mt-4 flex gap-2">
          <button 
            @click="testClick"
            class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Test Button
          </button>
          <span v-if="clicked" class="text-green-600 font-medium">
            Button clicked! Components are working.
          </span>
        </div>
      </div>
      
      <!-- Try to load a simple call center component -->
      <div v-if="showComponents" class="space-y-6">
        <ActiveCallsWidget />
        <RecentCallsWidget />
      </div>
      
      <div v-else class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Components Loading...</h2>
        <p class="text-gray-600">Please wait while components are being loaded.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ActiveCallsWidget from '@/components/CallCenter/ActiveCallsWidget.vue'
import RecentCallsWidget from '@/components/CallCenter/RecentCallsWidget.vue'

const clicked = ref(false)
const showComponents = ref(false)

function testClick() {
  clicked.value = true
  console.log('Test button clicked')
}

onMounted(() => {
  // Simulate loading delay
  setTimeout(() => {
    showComponents.value = true
  }, 1000)
})
</script>