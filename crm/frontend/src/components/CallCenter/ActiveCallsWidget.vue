<template>
  <div class="bg-surface-white rounded-lg shadow p-4">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-ink-gray-9">Currently Calling</h3>
      <div class="flex items-center gap-2">
        <Badge
          v-if="activeCalls.length > 0"
          :variant="'solid'"
          :theme="'orange'"
          :label="`${activeCalls.length} Active`"
        />
        <FeatherIcon
          name="refresh-cw"
          class="size-4 cursor-pointer text-ink-gray-5 hover:text-ink-gray-7"
          @click="refreshActiveCalls"
        />
      </div>
    </div>

    <div v-if="activeCalls.length === 0" class="text-center py-8">
      <PhoneIcon class="size-12 mx-auto text-ink-gray-4 mb-2" />
      <p class="text-ink-gray-5">No active calls</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="call in activeCalls"
        :key="call.name"
        class="border border-outline-gray-2 rounded-lg p-3 hover:bg-surface-gray-1 transition-colors"
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
              <div class="absolute -bottom-1 -right-1">
                <div class="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
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
              {{ timeAgo(call.start_time) }}
            </div>
            <Badge
              v-if="call.status"
              :variant="'subtle'"
              :theme="getStatusTheme(call.status)"
              :label="call.status"
              class="mt-1"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { createResource } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { timeAgo } from '@/utils'
import UserAvatar from '@/components/UserAvatar.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { Badge, FeatherIcon } from 'frappe-ui'

const { getUser } = usersStore()

const activeCalls = ref([])

// Fetch active calls
const activeCallsResource = createResource({
  url: 'crm.api.call_center.get_active_calls',
  auto: true,
  onSuccess(data) {
    activeCalls.value = data || []
  }
})

function refreshActiveCalls() {
  activeCallsResource.reload()
}

function formatPhoneNumber(number) {
  if (!number) return ''
  // Simple phone number formatting
  return number.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3')
}

function getStatusTheme(status) {
  const themes = {
    'Initiated': 'blue',
    'Ringing': 'orange',
    'In Progress': 'green',
    'Routed': 'purple',
    'Queued': 'yellow'
  }
  return themes[status] || 'gray'
}

// Real-time updates via polling (can be enhanced with WebSocket later)
let pollingInterval = null

onMounted(() => {
  // Poll every 5 seconds for active calls
  pollingInterval = setInterval(() => {
    if (document.visibilityState === 'visible') {
      activeCallsResource.reload()
    }
  }, 5000)
})

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }
})
</script>