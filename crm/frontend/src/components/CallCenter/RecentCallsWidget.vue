<template>
  <div class="bg-surface-white rounded-lg shadow p-4">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-ink-gray-9">Recent Calls</h3>
      <div class="flex items-center gap-2">
        <select
          v-model="timeFilter"
          class="text-sm border border-outline-gray-2 rounded px-2 py-1"
          @change="loadRecentCalls"
        >
          <option value="today">Today</option>
          <option value="yesterday">Yesterday</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
        </select>
        <FeatherIcon
          name="refresh-cw"
          class="size-4 cursor-pointer text-ink-gray-5 hover:text-ink-gray-7"
          @click="loadRecentCalls"
        />
      </div>
    </div>

    <div v-if="recentCalls.loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
      <p class="text-ink-gray-5 mt-2">Loading calls...</p>
    </div>

    <div v-else-if="recentCalls.data?.length === 0" class="text-center py-8">
      <PhoneIcon class="size-12 mx-auto text-ink-gray-4 mb-2" />
      <p class="text-ink-gray-5">No recent calls</p>
    </div>

    <div v-else class="space-y-3 max-h-96 overflow-y-auto">
      <div
        v-for="call in recentCalls.data"
        :key="call.name"
        class="border border-outline-gray-2 rounded-lg p-3 hover:bg-surface-gray-1 transition-colors cursor-pointer"
        @click="viewCallDetails(call)"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="relative">
              <UserAvatar
                v-if="call.receiver"
                :user="call.receiver"
                size="sm"
              />
              <div
                v-else
                class="w-8 h-8 rounded-full bg-ink-gray-2 flex items-center justify-center"
              >
                <PhoneIcon class="size-4 text-ink-gray-5" />
              </div>
              <div
                v-if="call.status === 'Completed'"
                class="absolute -bottom-1 -right-1"
              >
                <div class="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <div
                v-else-if="call.status === 'Failed' || call.status === 'Busy'"
                class="absolute -bottom-1 -right-1"
              >
                <div class="w-3 h-3 rounded-full bg-red-500"></div>
              </div>
            </div>
            <div>
              <div class="font-medium text-ink-gray-9">
                {{ call.receiver ? getUser(call.receiver).full_name : 'Unassigned' }}
              </div>
              <div class="text-sm text-ink-gray-5 flex items-center gap-1">
                <PhoneIcon class="size-3" />
                {{ formatPhoneNumber(call.from_field) }}
              </div>
            </div>
          </div>
          <div class="text-right">
            <div class="text-sm text-ink-gray-5">
              {{ formatDate(call.start_time) }}
            </div>
            <div class="flex items-center gap-2 mt-1">
              <Badge
                v-if="call.status"
                :variant="'subtle'"
                :theme="getStatusTheme(call.status)"
                :label="call.status"
                class="text-xs"
              />
              <div
                v-if="call.duration && call.duration !== '00:00:00'"
                class="text-xs text-ink-gray-5 flex items-center gap-1"
              >
                <ClockIcon class="size-3" />
                {{ formatDuration(call.duration) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Call Details Modal -->
    <Dialog
      v-model="showCallDetails"
      :options="{ title: 'Call Details' }"
    >
      <template #body-content>
        <div v-if="selectedCall" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm text-ink-gray-5">Caller</label>
              <div class="font-medium">{{ formatPhoneNumber(selectedCall.from_field) }}</div>
            </div>
            <div>
              <label class="text-sm text-ink-gray-5">Agent</label>
              <div class="font-medium">
                {{ selectedCall.receiver ? getUser(selectedCall.receiver).full_name : 'Unassigned' }}
              </div>
            </div>
            <div>
              <label class="text-sm text-ink-gray-5">Status</label>
              <Badge
                :variant="'subtle'"
                :theme="getStatusTheme(selectedCall.status)"
                :label="selectedCall.status"
              />
            </div>
            <div>
              <label class="text-sm text-ink-gray-5">Duration</label>
              <div class="font-medium">{{ formatDuration(selectedCall.duration) }}</div>
            </div>
          </div>
          <div>
            <label class="text-sm text-ink-gray-5">Timestamp</label>
            <div class="font-medium">{{ formatDateTime(selectedCall.start_time) }}</div>
          </div>
          <div v-if="selectedCall.note">
            <label class="text-sm text-ink-gray-5">Notes</label>
            <div class="text-sm bg-surface-gray-1 p-2 rounded">
              {{ selectedCall.note }}
            </div>
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import UserAvatar from '@/components/UserAvatar.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import ClockIcon from '@/components/Icons/ClockIcon.vue'
import { Badge, FeatherIcon, Dialog } from 'frappe-ui'

const { getUser } = usersStore()

const timeFilter = ref('today')
const showCallDetails = ref(false)
const selectedCall = ref(null)

// Fetch recent calls
const recentCalls = createResource({
  url: 'crm.api.call_center.get_recent_calls',
  makeParams() {
    return {
      time_filter: timeFilter.value
    }
  },
  auto: true
})

function loadRecentCalls() {
  recentCalls.reload()
}

function viewCallDetails(call) {
  selectedCall.value = call
  showCallDetails.value = true
}

function formatPhoneNumber(number) {
  if (!number) return 'Unknown'
  return number.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3')
}

function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now - date)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 1) return 'Today'
  if (diffDays === 2) return 'Yesterday'
  return date.toLocaleDateString()
}

function formatDateTime(dateString) {
  return new Date(dateString).toLocaleString()
}

function formatDuration(duration) {
  if (!duration || duration === '00:00:00') return '0s'
  const [hours, minutes, seconds] = duration.split(':').map(Number)
  if (hours > 0) return `${hours}h ${minutes}m`
  if (minutes > 0) return `${minutes}m ${seconds}s`
  return `${seconds}s`
}

function getStatusTheme(status) {
  const themes = {
    'Completed': 'green',
    'Failed': 'red',
    'Busy': 'orange',
    'No Answer': 'yellow',
    'In Progress': 'blue',
    'Routed': 'purple'
  }
  return themes[status] || 'gray'
}

onMounted(() => {
  // Auto-refresh every 30 seconds
  setInterval(() => {
    if (document.visibilityState === 'visible') {
      recentCalls.reload()
    }
  }, 30000)
})
</script>