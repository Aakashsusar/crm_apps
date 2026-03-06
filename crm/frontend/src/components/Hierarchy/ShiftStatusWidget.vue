<template>
  <div v-if="shiftInfo" class="shift-status-widget" :class="statusClass">
    <div class="shift-icon">
      <ClockIcon class="icon" />
    </div>
    <div class="shift-details">
      <div class="shift-name">{{ shiftInfo.shift_name }}</div>
      <div class="shift-time">{{ shiftInfo.start_time }} - {{ shiftInfo.end_time }}</div>
      <div v-if="isActive" class="remaining-time">
        <span class="dot"></span>
        {{ remainingMinutes }} min remaining
      </div>
      <div v-else class="inactive-status">
        Shift Inactive
      </div>
    </div>
  </div>
  <div v-else class="shift-status-widget no-shift">
    <div class="shift-icon">
      <AlertCircleIcon class="icon" />
    </div>
    <div class="shift-details">
      <div class="shift-name">No Shift Assigned</div>
      <div class="shift-time">Contact your manager</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import { Clock as ClockIcon, AlertCircle as AlertCircleIcon } from 'lucide-vue-next'

const shiftInfo = ref(null)
const isActive = ref(false)
const remainingMinutes = ref(0)
let intervalId = null

const statusClass = computed(() => {
  if (!isActive.value) return 'inactive'
  if (remainingMinutes.value < 30) return 'ending-soon'
  return 'active'
})

const hierarchyResource = createResource({
  url: 'crm.api.hierarchy.get_user_hierarchy',
  auto: true,
  onSuccess(data) {
    shiftInfo.value = data.shift
    isActive.value = data.is_shift_active
    remainingMinutes.value = data.remaining_minutes
  }
})

function startTimer() {
  // Update every minute
  intervalId = setInterval(() => {
    hierarchyResource.reload()
  }, 60000) // 60 seconds
}

onMounted(() => {
  startTimer()
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.shift-status-widget {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  background: white;
}

.shift-status-widget.active {
  border-color: #10b981;
  background: #ecfdf5;
}

.shift-status-widget.ending-soon {
  border-color: #f59e0b;
  background: #fffbeb;
}

.shift-status-widget.inactive {
  border-color: #ef4444;
  background: #fef2f2;
}

.shift-status-widget.no-shift {
  border-color: #6b7280;
  background: #f9fafb;
}

.shift-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
}

.active .shift-icon {
  background: #10b981;
  color: white;
}

.ending-soon .shift-icon {
  background: #f59e0b;
  color: white;
}

.inactive .shift-icon {
  background: #ef4444;
  color: white;
}

.no-shift .shift-icon {
  background: #6b7280;
  color: white;
}

.shift-icon .icon {
  width: 1.5rem;
  height: 1.5rem;
}

.shift-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.shift-name {
  font-weight: 600;
  font-size: 0.9375rem;
  color: #111827;
}

.shift-time {
  font-size: 0.8125rem;
  color: #6b7280;
}

.remaining-time {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
}

.active .remaining-time {
  color: #10b981;
}

.ending-soon .remaining-time {
  color: #f59e0b;
}

.remaining-time .dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.active .remaining-time .dot {
  background: #10b981;
}

.ending-soon .remaining-time .dot {
  background: #f59e0b;
}

.inactive-status {
  font-size: 0.8125rem;
  color: #ef4444;
  font-weight: 500;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
