<template>
  <div class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-surface-gray-1 cursor-pointer transition-colors"
       @click="toggleCallStatus"
  >
    <div class="relative">
      <PhoneIcon 
        class="size-4" 
        :class="getStatusColor(currentStatus)"
      />
      <div 
        v-if="currentStatus !== 'Available'"
        class="absolute -bottom-1 -right-1 w-2 h-2 rounded-full"
        :class="getStatusIndicatorColor(currentStatus)"
      ></div>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium text-ink-gray-9 truncate">
        {{ getStatusLabel(currentStatus) }}
      </div>
      <div v-if="currentCall" class="text-xs text-ink-gray-5 truncate">
        {{ formatPhoneNumber(currentCall.from_field) }}
      </div>
    </div>
    <ChevronDownIcon class="size-3 text-ink-gray-4" />
  </div>

  <!-- Status Dropdown -->
  <Dialog
    v-model="showStatusDialog"
    :options="{ title: 'Call Status' }"
  >
    <template #body-content>
      <div class="space-y-3">
        <div>
          <label class="text-sm font-medium text-ink-gray-7 mb-2 block">Set Your Status</label>
          <div class="grid grid-cols-2 gap-2">
            <Button
              v-for="status in availableStatuses"
              :key="status.value"
              :variant="currentStatus === status.value ? 'solid' : 'outline'"
              :theme="status.theme"
              size="sm"
              class="w-full"
              @click="setStatus(status.value)"
            >
              <component :is="status.icon" class="size-3 mr-1" />
              {{ status.label }}
            </Button>
          </div>
        </div>

        <div v-if="currentCall" class="border-t border-outline-gray-2 pt-3">
          <label class="text-sm font-medium text-ink-gray-7 mb-2 block">Current Call</label>
          <div class="bg-blue-50 p-3 rounded-lg">
            <div class="flex items-center justify-between">
              <div>
                <div class="font-medium text-ink-gray-9">
                  {{ formatPhoneNumber(currentCall.from_field) }}
                </div>
                <div class="text-sm text-ink-gray-5">
                  Started {{ timeAgo(currentCall.start_time) }}
                </div>
              </div>
              <Badge
                :variant="'subtle'"
                :theme="getStatusTheme(currentCall.status)"
                :label="currentCall.status"
              />
            </div>
          </div>
        </div>

        <div class="border-t border-outline-gray-2 pt-3">
          <label class="text-sm font-medium text-ink-gray-7 mb-2 block">Quick Actions</label>
          <div class="flex gap-2">
            <Button
              v-if="currentStatus === 'In Call'"
              variant="outline"
              size="sm"
              @click="endCurrentCall"
            >
              <XIcon class="size-3 mr-1" />
              End Call
            </Button>
            <Button
              variant="outline"
              size="sm"
              @click="viewCallHistory"
            >
              <HistoryIcon class="size-3 mr-1" />
              History
            </Button>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import { globalStore } from '@/stores/global'
import { timeAgo } from '@/utils'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import ChevronDownIcon from '@/components/Icons/ChevronDownIcon.vue'
import XIcon from '@/components/Icons/XIcon.vue'
import HistoryIcon from '@/components/Icons/HistoryIcon.vue'
import { Button, Badge, Dialog } from 'frappe-ui'

const { user } = globalStore()

const showStatusDialog = ref(false)
const currentStatus = ref('Available')
const currentCall = ref(null)

const availableStatuses = [
  {
    value: 'Available',
    label: 'Available',
    theme: 'green',
    icon: PhoneIcon
  },
  {
    value: 'Busy',
    label: 'Busy',
    theme: 'red',
    icon: PhoneIcon
  },
  {
    value: 'In Call',
    label: 'In Call',
    theme: 'blue',
    icon: PhoneIcon
  },
  {
    value: 'Do Not Disturb',
    label: 'DND',
    theme: 'orange',
    icon: PhoneIcon
  }
]

// Fetch agent status
const agentStatusResource = createResource({
  url: 'crm.api.call_center.get_agent_status',
  makeParams() {
    return {
      agent: user.value
    }
  },
  auto: true,
  onSuccess(data) {
    currentStatus.value = data?.status || 'Available'
    currentCall.value = data?.current_call || null
  }
})

// Update agent status
const updateStatusResource = createResource({
  url: 'crm.api.call_center.update_agent_status',
  onSuccess() {
    agentStatusResource.reload()
    showStatusDialog.value = false
  }
})

// End current call
const endCallResource = createResource({
  url: 'crm.api.call_center.end_call',
  onSuccess() {
    agentStatusResource.reload()
  }
})

function toggleCallStatus() {
  showStatusDialog.value = true
}

function setStatus(status) {
  updateStatusResource.submit({
    agent: user.value,
    status: status
  })
}

function endCurrentCall() {
  if (currentCall.value) {
    endCallResource.submit({
      call_name: currentCall.value.name
    })
  }
}

function viewCallHistory() {
  // Navigate to call history page
  // router.push({ name: 'CallHistory' })
  showStatusDialog.value = false
}

function getStatusLabel(status) {
  const labels = {
    'Available': 'Available for Calls',
    'Busy': 'Busy',
    'In Call': 'In Call',
    'Do Not Disturb': 'Do Not Disturb'
  }
  return labels[status] || status
}

function getStatusColor(status) {
  const colors = {
    'Available': 'text-green-600',
    'Busy': 'text-red-600',
    'In Call': 'text-blue-600',
    'Do Not Disturb': 'text-orange-600'
  }
  return colors[status] || 'text-ink-gray-5'
}

function getStatusIndicatorColor(status) {
  const colors = {
    'Available': 'bg-green-500',
    'Busy': 'bg-red-500',
    'In Call': 'bg-blue-500',
    'Do Not Disturb': 'bg-orange-500'
  }
  return colors[status] || 'bg-ink-gray-4'
}

function getStatusTheme(status) {
  const themes = {
    'In Progress': 'green',
    'Ringing': 'orange',
    'Queued': 'yellow',
    'Completed': 'blue'
  }
  return themes[status] || 'gray'
}

function formatPhoneNumber(number) {
  if (!number) return 'Unknown'
  return number.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3')
}

// Real-time status updates
let pollingInterval = null

onMounted(() => {
  pollingInterval = setInterval(() => {
    if (document.visibilityState === 'visible' && user.value) {
      agentStatusResource.reload()
    }
  }, 5000) // Poll every 5 seconds
})

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }
})
</script>