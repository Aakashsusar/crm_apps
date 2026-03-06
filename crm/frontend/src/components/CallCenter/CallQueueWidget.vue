<template>
  <div class="bg-surface-white rounded-lg shadow p-4">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-ink-gray-9">Call Queue</h3>
      <div class="flex items-center gap-2">
        <Badge
          v-if="queueStats.total > 0"
          :variant="'solid'"
          :theme="queueStats.total > 5 ? 'red' : queueStats.total > 2 ? 'orange' : 'yellow'"
          :label="`${queueStats.total} Waiting`"
        />
        <FeatherIcon
          name="refresh-cw"
          class="size-4 cursor-pointer text-ink-gray-5 hover:text-ink-gray-7"
          @click="refreshQueue"
        />
      </div>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-4 text-center">
      <div class="bg-blue-50 p-3 rounded-lg">
        <div class="text-2xl font-bold text-blue-600">{{ queueStats.queued }}</div>
        <div class="text-sm text-blue-800">Queued</div>
      </div>
      <div class="bg-orange-50 p-3 rounded-lg">
        <div class="text-2xl font-bold text-orange-600">{{ queueStats.ringing }}</div>
        <div class="text-sm text-orange-800">Ringing</div>
      </div>
      <div class="bg-green-50 p-3 rounded-lg">
        <div class="text-2xl font-bold text-green-600">{{ queueStats.in_progress }}</div>
        <div class="text-sm text-green-800">In Progress</div>
      </div>
    </div>

    <div v-if="callQueue.length === 0" class="text-center py-8">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-100 mb-3">
        <CheckIcon class="size-6 text-green-600" />
      </div>
      <p class="text-ink-gray-5">No calls in queue</p>
      <p class="text-sm text-ink-gray-4 mt-1">All systems operational</p>
    </div>

    <div v-else class="space-y-3 max-h-64 overflow-y-auto">
      <div
        v-for="(call, index) in callQueue"
        :key="call.name"
        class="border border-outline-gray-2 rounded-lg p-3 hover:bg-surface-gray-1 transition-colors"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="flex-shrink-0 w-8 text-center">
              <span class="text-sm font-medium text-ink-gray-5">#{{ index + 1 }}</span>
            </div>
            <div>
              <div class="font-medium text-ink-gray-9">
                {{ formatPhoneNumber(call.from_field) }}
              </div>
              <div class="text-sm text-ink-gray-5">
                Waiting: {{ timeInQueue(call.start_time) }}
              </div>
            </div>
          </div>
          <div class="text-right">
            <div class="flex items-center gap-2">
              <Badge
                :variant="'subtle'"
                :theme="getStatusTheme(call.status)"
                :label="call.status"
              />
              <div
                v-if="call.status === 'Queued'"
                class="w-2 h-2 rounded-full bg-orange-500 animate-pulse"
              ></div>
            </div>
            <div class="text-xs text-ink-gray-5 mt-1">
              {{ formatTime(call.start_time) }}
            </div>
          </div>
        </div>
        
        <!-- Queue Position Indicator -->
        <div class="mt-2">
          <div class="flex items-center gap-2">
            <div class="flex-1 h-1.5 bg-surface-gray-2 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-500 rounded-full transition-all duration-300"
                :style="{ width: `${getProgressPercentage(index + 1)}%` }"
              ></div>
            </div>
            <span class="text-xs text-ink-gray-5">Position {{ index + 1 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Queue Management Actions -->
    <div v-if="callQueue.length > 0" class="mt-4 pt-4 border-t border-outline-gray-2">
      <div class="flex gap-2">
        <Button
          v-if="queueStats.queued > 0"
          variant="outline"
          :loading="assignAgentResource.loading"
          @click="assignNextCall"
        >
          <PhoneIcon class="size-4 mr-1" />
          Assign Next Call
        </Button>
        <Button
          variant="subtle"
          @click="clearCompletedCalls"
        >
          <TrashIcon class="size-4 mr-1" />
          Clear Completed
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import TrashIcon from '@/components/Icons/TrashIcon.vue'
import { Badge, FeatherIcon, Button } from 'frappe-ui'

const callQueue = ref([])
const queueStats = ref({
  total: 0,
  queued: 0,
  ringing: 0,
  in_progress: 0
})

// Fetch call queue
const queueResource = createResource({
  url: 'crm.api.call_center.get_call_queue',
  auto: true,
  onSuccess(data) {
    callQueue.value = data.calls || []
    queueStats.value = data.stats || {
      total: 0,
      queued: 0,
      ringing: 0,
      in_progress: 0
    }
  }
})

// Assign next call to available agent
const assignAgentResource = createResource({
  url: 'crm.api.call_center.assign_next_call',
  onSuccess() {
    refreshQueue()
  }
})

function refreshQueue() {
  queueResource.reload()
}

function assignNextCall() {
  assignAgentResource.submit()
}

function clearCompletedCalls() {
  createResource({
    url: 'crm.api.call_center.clear_completed_calls',
    auto: true,
    onSuccess() {
      refreshQueue()
    }
  })
}

function formatPhoneNumber(number) {
  if (!number) return 'Unknown'
  return number.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3')
}

function timeInQueue(startTime) {
  const start = new Date(startTime)
  const now = new Date()
  const diffSeconds = Math.floor((now - start) / 1000)
  
  if (diffSeconds < 60) return `${diffSeconds}s`
  const minutes = Math.floor(diffSeconds / 60)
  const seconds = diffSeconds % 60
  return `${minutes}m ${seconds}s`
}

function formatTime(dateTime) {
  return new Date(dateTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function getProgressPercentage(position) {
  if (callQueue.value.length === 0) return 0
  // Higher position means lower percentage (further from front)
  return ((callQueue.value.length - position + 1) / callQueue.value.length) * 100
}

function getStatusTheme(status) {
  const themes = {
    'Queued': 'yellow',
    'Ringing': 'orange',
    'In Progress': 'green',
    'Failed': 'red'
  }
  return themes[status] || 'gray'
}

// Real-time updates
let pollingInterval = null

onMounted(() => {
  pollingInterval = setInterval(() => {
    if (document.visibilityState === 'visible') {
      queueResource.reload()
    }
  }, 10000) // Poll every 10 seconds for queue updates
})

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }
})
</script>