<template>
  <div v-show="showCallPopup" v-bind="$attrs">
    <div
      ref="callPopup"
      class="fixed z-20 flex w-60 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 text-ink-gray-2 shadow-2xl"
      :style="style"
    >
      <div class="flex flex-row-reverse items-center gap-1">
        <MinimizeIcon
          class="h-4 w-4 cursor-pointer"
          @click="toggleCallWindow"
        />
      </div>
      <div class="flex flex-col items-center justify-center gap-3">
        <Avatar
          v-if="contact?.image"
          :image="contact.image"
          :label="contact.full_name"
          class="relative flex !h-24 !w-24 items-center justify-center [&>div]:text-[30px]"
          :class="onCall || calling ? '' : 'pulse'"
        />
        <div class="flex flex-col items-center justify-center gap-1">
          <div class="text-xl font-medium">
            {{ contact?.full_name ?? __('Unknown') }}
          </div>
          <div class="text-sm text-ink-gray-5">{{ contact?.mobile_no }}</div>
        </div>
        <CountUpTimer ref="counterUp">
          <div v-if="onCall" class="my-1 text-base">
            {{ counterUp?.updatedTime }}
          </div>
        </CountUpTimer>
        <div v-if="!onCall" class="my-1 text-base">
          {{
            callStatus == 'Initiated'
              ? __('Initiating call...')
              : callStatus == 'Ringing'
                ? __('Ringing...')
                : calling
                  ? __('Calling...')
                  : __('Connecting...')
          }}
        </div>
        <div v-if="onCall" class="flex gap-2">
          <Button
            class="cursor-pointer rounded-full"
            :tooltip="__('Add a note')"
            :icon="NoteIcon"
            @click="showNoteModal = true"
          />
          <Button
            class="rounded-full bg-surface-red-5 hover:bg-surface-red-6 rotate-[135deg] text-ink-white"
            :tooltip="__('Hang up')"
            :icon="PhoneIcon"
            @click="hangUpCall"
          />
        </div>
        <div v-else-if="calling || callStatus == 'Initiated'">
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Cancel')"
            @click="cancelCall"
            class="rounded-lg text-ink-white"
            :disabled="callStatus == 'Initiated' && !callId"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
      </div>
    </div>
  </div>
  <div
    v-show="showSmallCallWindow"
    class="ml-2 flex cursor-pointer select-none items-center justify-between gap-3 rounded-lg bg-surface-gray-7 px-2 py-[7px] text-base text-ink-gray-2"
    @click="toggleCallWindow"
    v-bind="$attrs"
  >
    <div class="flex items-center gap-2">
      <Avatar
        v-if="contact?.image"
        :image="contact.image"
        :label="contact.full_name"
        class="relative flex !h-5 !w-5 items-center justify-center"
      />
      <div class="max-w-[120px] truncate">
        {{ contact?.full_name ?? __('Unknown') }}
      </div>
    </div>
    <div v-if="onCall" class="flex items-center gap-2">
      <div class="my-1 min-w-[40px] text-center">
        {{ counterUp?.updatedTime }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-white"
        :icon="PhoneIcon"
        @click.stop="hangUpCall"
      />
    </div>
    <div v-else-if="calling" class="flex items-center gap-3">
      <div class="my-1">
        {{ callStatus == 'Ringing' ? __('Ringing...') : __('Calling...') }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full rotate-[135deg] text-ink-white"
        :icon="PhoneIcon"
        @click.stop="cancelCall"
      />
    </div>
  </div>
  <NoteModal
    v-model="showNoteModal"
    :note="note"
    doctype="CRM Call Log"
    @after="updateNote"
  />
</template>

<script setup>
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { capture } from '@/telemetry'
import { Avatar, call, createResource, createToast } from 'frappe-ui'
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { globalStore } from '@/stores/global'

const store = globalStore()

let showCallPopup = ref(false)
let showSmallCallWindow = ref(false)
let onCall = ref(false)
let calling = ref(false)
let callPopup = ref(null)
let counterUp = ref(null)
let callStatus = ref('')
let callId = ref('')
let refId = ref('')

const phoneNumber = ref('')

const contact = ref({
  full_name: '',
  image: '',
  mobile_no: '',
})

watch(phoneNumber, (value) => {
  if (!value) return
  getContact.fetch()
})

const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return {
      phone_number: phoneNumber.value,
    }
  },
  cache: ['contact', phoneNumber.value],
  onSuccess(data) {
    contact.value = data
  },
})

const showNoteModal = ref(false)
const note = ref({
  name: '',
  title: '',
  content: '',
})

async function updateNote(_note, insert_mode = false) {
  note.value = _note
  if (insert_mode && _note.name && refId.value) {
    await call('crm.integrations.api.add_note_to_call_log', {
      ref_id: refId.value,
      note: _note,
    })
  }
}

const { width, height } = useWindowSize()

let { style } = useDraggable(callPopup, {
  initialValue: { x: width.value - 280, y: height.value - 310 },
  preventDefault: true,
})

// Real-time status updates via socket
function setupRealtimeListener() {
  if (!store.$socket) return

  store.$socket.on('tata_tele_call', (data) => {
    console.log('[TATA TELE] Real-time update:', data)
    
    if (data.ref_id !== refId.value) return

    // Update call status
    if (data.status) {
      callStatus.value = data.status
      
      // Handle different statuses
      if (data.status === 'Ringing') {
        calling.value = true
        onCall.value = false
      } else if (data.status === 'In Progress') {
        calling.value = false
        onCall.value = true
        if (counterUp.value && !counterUp.value.isRunning) {
          counterUp.value.start()
        }
      } else if (['Completed', 'No answer', 'Failed', 'Busy', 'Cancelled'].includes(data.status)) {
        handleCallEnd(data.status, data.duration)
      }
    }

    // Update duration if provided
    if (data.duration && onCall.value) {
      // Duration is already being tracked by CountUpTimer
      console.log('[TATA TELE] Call duration:', data.duration)
    }
  })
}

function handleCallEnd(status, duration) {
  console.log('[TATA TELE] Call ended:', status, 'Duration:', duration)
  
  calling.value = false
  onCall.value = false
  showCallPopup.value = false
  showSmallCallWindow.value = false
  
  if (counterUp.value) {
    counterUp.value.stop()
  }
  
  // Show toast notification
  const toast = createToast({
    title: __('Call Ended'),
    text: status === 'Completed' 
      ? __('Call completed successfully') 
      : __('Call ended: {0}', [status]),
    icon: 'phone',
    iconClasses: status === 'Completed' ? 'text-green-500' : 'text-gray-500',
  })
  toast.show()
  
  // Reset state
  callStatus.value = ''
  callId.value = ''
  refId.value = ''
  note.value = {
    name: '',
    title: '',
    content: '',
  }
}

async function makeOutgoingCall(number) {
  console.log("=" .repeat(80))
  console.log('[TATA TELE] makeOutgoingCall called')
  console.log('[TATA TELE] Number:', number)
  console.log('[TATA TELE] Current state - calling:', calling.value, 'onCall:', onCall.value)
  
  phoneNumber.value = number

  try {
    console.log('[TATA TELE] Calling API: crm.integrations.tata_tele.handler.make_a_call')
    console.log('[TATA TELE] Parameters:', { to_number: number })
    
    const response = await call('crm.integrations.tata_tele.handler.make_a_call', {
      to_number: number,
    })

    console.log('[TATA TELE] API Response:', response)

    if (response.success || response.ok) {
      refId.value = response.ref_id
      callId.value = response.call_id
      callStatus.value = 'Initiated'
      
      console.log('[TATA TELE] Call initiated successfully')
      console.log('[TATA TELE] ref_id:', refId.value)
      console.log('[TATA TELE] call_id:', callId.value)
      console.log('[TATA TELE] Showing call popup...')
      
      showCallPopup.value = true
      calling.value = true
      onCall.value = false

      capture('make_outgoing_call_tata_tele')

      const toast = createToast({
        title: __('Call Initiated'),
        text: __('Connecting to {0}...', [number]),
        icon: 'phone',
        iconClasses: 'text-blue-500',
      })
      toast.show()
      
      console.log('[TATA TELE] UI updated - popup shown, waiting for status updates...')
    } else {
      console.error('[TATA TELE] API returned unsuccessful response:', response)
      throw new Error(response.message || 'Failed to initiate call')
    }
  } catch (error) {
    console.error('[TATA TELE] Call error:', error)
    console.error('[TATA TELE] Error stack:', error.stack)
    
    const toast = createToast({
      title: __('Call Failed'),
      text: error.message || __('Could not connect call'),
      icon: 'x',
      iconClasses: 'text-red-500',
    })
    toast.show()
    
    // Reset state
    showCallPopup.value = false
    calling.value = false
    onCall.value = false
    callStatus.value = ''
  }
  
  console.log("=" .repeat(80))
}

async function cancelCall() {
  if (!callId.value) {
    console.warn('[TATA TELE] No call_id available for cancellation')
    showCallPopup.value = false
    showSmallCallWindow.value = false
    calling.value = false
    onCall.value = false
    callStatus.value = ''
    return
  }

  try {
    console.log('[TATA TELE] Cancelling call:', callId.value)
    
    const response = await call('crm.integrations.tata_tele.handler.hangup_call', {
      call_id: callId.value,
      ref_id: refId.value,
    })

    console.log('[TATA TELE] Call cancelled:', response)

    const toast = createToast({
      title: __('Call Cancelled'),
      text: __('Call has been cancelled'),
      icon: 'phone-off',
      iconClasses: 'text-gray-500',
    })
    toast.show()
  } catch (error) {
    console.error('[TATA TELE] Cancel error:', error)
    
    const toast = createToast({
      title: __('Cancel Failed'),
      text: error.message || __('Could not cancel call'),
      icon: 'x',
      iconClasses: 'text-red-500',
    })
    toast.show()
  } finally {
    // Always reset UI state
    showCallPopup.value = false
    showSmallCallWindow.value = false
    calling.value = false
    onCall.value = false
    callStatus.value = ''
    callId.value = ''
    refId.value = ''
    note.value = {
      name: '',
      title: '',
      content: '',
    }
  }
}

async function hangUpCall() {
  await cancelCall()
}

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value
  showSmallCallWindow.value = !showSmallCallWindow.value
}

onMounted(() => {
  console.log('[TATA TELE] Component mounted, setting up realtime listener')
  setupRealtimeListener()
})

onUnmounted(() => {
  if (store.$socket) {
    store.$socket.off('tata_tele_call')
  }
})

function setup() {
  console.log('[TATA TELE] Setup function called')
  setupRealtimeListener()
}

defineExpose({ makeOutgoingCall, setup })
</script>

<style scoped>
.pulse::before {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
}

.pulse::after {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }

  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}
</style>
