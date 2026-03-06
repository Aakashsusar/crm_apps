<template>
  <div
    v-if="incomingCall"
    class="fixed top-4 right-4 z-50 w-80 bg-surface-white rounded-lg shadow-xl border border-outline-gray-2 animate-slide-in-right"
  >
    <div class="p-4">
      <div class="flex items-start justify-between mb-3">
        <div class="flex items-center gap-3">
          <div class="relative">
            <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <PhoneIcon class="size-6 text-blue-600 animate-pulse" />
            </div>
            <div class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full animate-ping"></div>
          </div>
          <div>
            <h3 class="font-semibold text-ink-gray-9">Incoming Call</h3>
            <p class="text-sm text-ink-gray-5">New call routed to you</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          @click="dismissCall"
        >
          <XIcon class="size-4" />
        </Button>
      </div>

      <div class="mb-4 p-3 bg-blue-50 rounded-lg">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-ink-gray-7">Caller</span>
          <Badge variant="subtle" theme="blue" label="Incoming" />
        </div>
        <div class="text-lg font-semibold text-ink-gray-9">
          {{ formatPhoneNumber(incomingCall.from_field) }}
        </div>
        <div class="text-sm text-ink-gray-5 mt-1">
          {{ timeAgo(incomingCall.start_time) }}
        </div>
      </div>

      <div class="flex gap-2">
        <Button
          variant="solid"
          theme="green"
          class="flex-1"
          :loading="answerCallResource.loading"
          @click="answerCall"
        >
          <PhoneIcon class="size-4 mr-1" />
          Answer
        </Button>
        <Button
          variant="outline"
          theme="red"
          class="flex-1"
          :loading="rejectCallResource.loading"
          @click="rejectCall"
        >
          <XIcon class="size-4 mr-1" />
          Reject
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import { globalStore } from '@/stores/global'
import { timeAgo } from '@/utils'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import XIcon from '@/components/Icons/XIcon.vue'
import { Button, Badge } from 'frappe-ui'

const { user } = globalStore()

const incomingCall = ref(null)

// Check for incoming calls
const incomingCallResource = createResource({
  url: 'crm.api.call_center.get_incoming_call_for_agent',
  makeParams() {
    return {
      agent: user.value
    }
  },
  onSuccess(data) {
    if (data) {
      incomingCall.value = data
      // Auto-dismiss after 30 seconds
      setTimeout(() => {
        if (incomingCall.value && incomingCall.value.name === data.name) {
          dismissCall()
        }
      }, 30000)
    }
  }
})

// Answer call
const answerCallResource = createResource({
  url: 'crm.api.call_center.answer_call',
  onSuccess() {
    dismissCall()
    // Optional: Show success notification
  }
})

// Reject call
const rejectCallResource = createResource({
  url: 'crm.api.call_center.reject_call',
  onSuccess() {
    dismissCall()
    // Optional: Show rejection notification
  }
})

function answerCall() {
  if (incomingCall.value) {
    answerCallResource.submit({
      call_name: incomingCall.value.name
    })
  }
}

function rejectCall() {
  if (incomingCall.value) {
    rejectCallResource.submit({
      call_name: incomingCall.value.name
    })
  }
}

function dismissCall() {
  incomingCall.value = null
}

function formatPhoneNumber(number) {
  if (!number) return 'Unknown'
  return number.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3')
}

// Real-time polling for incoming calls
let pollingInterval = null

onMounted(() => {
  // Check for incoming calls every 3 seconds
  pollingInterval = setInterval(() => {
    if (document.visibilityState === 'visible' && user.value) {
      incomingCallResource.reload()
    }
  }, 3000)
})

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }
})
</script>

<style scoped>
@keyframes slide-in-right {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}
</style>