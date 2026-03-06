<template>
  <div>
    <!-- Small popup -->
    <div
      v-show="showSmallCallPopup"
      class="ml-2 flex cursor-pointer select-none items-center justify-between gap-1 rounded-full bg-surface-gray-7 px-2 py-[7px] text-base text-ink-gray-2"
      @click="toggleCallPopup"
    >
      <div class="flex justify-center items-center size-5 rounded-full bg-surface-gray-6 shrink-0 mr-1">
        <Avatar
          v-if="contact?.image"
          :image="contact.image"
          :label="contact.full_name"
          class="!size-5"
        />
        <AvatarIcon v-else class="size-3" />
      </div>

      <span>{{ contact?.full_name ?? contact?.mobile_no }}</span>
      <span>·</span>

      <div v-if="uiStatus === 'In progress'">
        {{ prettyTime }}
      </div>

      <div v-else class="text-ink-gray-5">
        {{ uiStatus }}
      </div>

      <FeatherIcon
        name="x"
        class="size-3 ml-1 cursor-pointer text-ink-gray-5"
        @click.stop="closePopupOnly"
      />
    </div>

    <!-- Full popup -->
    <div
      v-show="showCallPopup"
      ref="callPopupHeader"
      class="fixed bottom-5 right-5 z-50 w-80 rounded-lg bg-surface-modal shadow-lg border border-outline-gray-modals flex flex-col"
      :style="style"
    >
      <div class="header flex justify-between items-center p-4 border-b border-outline-gray-modals">
        <div class="flex items-center gap-3 flex-1">
          <Avatar
            v-if="contact?.image"
            :image="contact.image"
            :label="contact.full_name"
            class="!size-10"
          />
          <div v-else class="flex justify-center items-center size-10 rounded-full bg-surface-gray-6">
            <AvatarIcon class="size-4" />
          </div>

          <div class="flex flex-col gap-1">
            <div class="font-medium text-ink-gray-9">
              {{ contact?.full_name ?? contact?.mobile_no }}
            </div>
            <div class="text-sm text-ink-gray-5">{{ contact?.mobile_no }}</div>
          </div>
        </div>

        <Button
          variant="ghost"
          icon="minimize-2"
          class="text-ink-gray-5"
          @click="toggleCallPopup"
        />
      </div>

      <div class="body flex-1 flex flex-col items-center justify-center gap-3 p-6">
        <div class="text-center">
          <div class="text-2xl font-semibold text-ink-gray-9">
            {{ contact?.full_name ?? __('Call') }}
          </div>

          <div class="text-base text-ink-gray-5 mt-2">
            {{ uiStatus }}
          </div>

          <div v-if="uiStatus === 'In progress'" class="text-3xl font-semibold text-ink-gray-9 mt-3">
            {{ prettyTime }}
          </div>
        </div>

        <div class="flex gap-2 mt-4">
          <!-- Cancel / Hangup -->
          <Button
            v-if="canCancel"
            variant="solid"
            theme="red"
            class="rounded-full !h-12 !w-12"
            :icon="PhoneIcon"
            @click="cancelCall"
          />
        </div>
      </div>

      <div class="footer flex justify-between gap-2 p-4 border-t border-outline-gray-modals">
        <Button
          class="flex-1"
          variant="ghost"
          :label="__('Add note')"
          :icon="NoteIcon"
          @click="showNoteWindow"
        />
        <Button
          class="flex-1"
          variant="ghost"
          :label="__('Add task')"
          :icon="TaskIcon"
          @click="showTaskWindow"
        />
      </div>
    </div>

    <NoteModal
      v-model="showNoteModal"
      :note="note"
      doctype="CRM Call Log"
      @after="updateNote"
    />

    <TaskModal
      v-model="showTaskModal"
      :task="task"
      doctype="CRM Call Log"
      @after="updateTask"
    />
  </div>
</template>

<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AvatarIcon from '@/components/Icons/AvatarIcon.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import TaskModal from '@/components/Modals/TaskModal.vue'
import { useDraggable, useWindowSize } from '@vueuse/core'
import { Avatar, Button, FeatherIcon, call, createResource, toast } from 'frappe-ui'
import { ref, computed, watch, onBeforeUnmount } from 'vue'

const showCallPopup = ref(false)
const showSmallCallPopup = ref(false)
const showNoteModal = ref(false)
const showTaskModal = ref(false)
const loading = ref(false)

const phoneNumber = ref('')
const contact = ref({ full_name: '', image: '', mobile_no: '' })

// IMPORTANT: track by ref_id (call_id can be null initially)
const currentRefId = ref('')
const providerCallId = ref(null)

const uiStatus = ref('') // "Calling...", "Ringing...", "In progress", "Call ended", "No answer", etc.

const callPopupHeader = ref(null)
const { width, height } = useWindowSize()
let { style } = useDraggable(callPopupHeader, {
  initialValue: { x: width.value - 350, y: height.value - 250 },
  preventDefault: true,
})

// --- Contact fetch
const getContact = createResource({
  url: 'crm.integrations.api.get_contact_by_phone_number',
  makeParams() {
    return { phone_number: phoneNumber.value }
  },
  onSuccess(data) {
    contact.value = data || contact.value
  },
})

watch(phoneNumber, (value) => {
  if (!value) return
  getContact.fetch()
})

/* -------------------------------------------------------
   Timer (simple local timer)
------------------------------------------------------- */
const seconds = ref(0)
let timer = null

const prettyTime = computed(() => {
  const s = seconds.value
  const mm = String(Math.floor(s / 60)).padStart(2, '0')
  const ss = String(s % 60).padStart(2, '0')
  return `${mm}:${ss}`
})

function startTimer() {
  stopTimer()
  seconds.value = 0
  timer = setInterval(() => {
    seconds.value += 1
  }, 1000)
}

function stopTimer() {
  if (timer) clearInterval(timer)
  timer = null
}

onBeforeUnmount(() => stopTimer())

const canCancel = computed(() => {
  return ['Calling...', 'Ringing...', 'In progress'].includes(uiStatus.value) && !!currentRefId.value
})

/* -------------------------------------------------------
   Outgoing Call
------------------------------------------------------- */
function makeOutgoingCall(number) {
  loading.value = true
  phoneNumber.value = number
  uiStatus.value = 'Initiating...'
  showCallPopup.value = true
  showSmallCallPopup.value = false
  currentRefId.value = ''
  providerCallId.value = null
  stopTimer()

  call('crm.integrations.tata_tele.handler.make_a_call', { to_number: phoneNumber.value })
    .then((response) => {
      loading.value = false

      if (response && response.ok) {
        // Track by ref_id
        currentRefId.value = response.ref_id
        providerCallId.value = response.call_id || null

        uiStatus.value = 'Calling...'
        toast.success(__('Call initiated successfully to {0}', [phoneNumber.value]))
      } else {
        uiStatus.value = 'Call failed'
        toast.error(response?.message || __('Failed to initiate call'))
      }
    })
    .catch((err) => {
      loading.value = false
      uiStatus.value = 'Call failed'
      toast.error(err?.message || __('Failed to initiate call'))
    })
}

/* -------------------------------------------------------
   Cancel / Hangup
------------------------------------------------------- */
function cancelCall() {
  if (!currentRefId.value) return

  // If no provider call_id yet, just close UI
  if (!providerCallId.value) {
    uiStatus.value = 'Cancelled'
    stopTimer()
    toast.success(__('Call cancelled'))
    autoCloseSoon()
    return
  }

  loading.value = true
  call('crm.integrations.tata_tele.handler.hangup_call', {
    call_id: providerCallId.value,
    ref_id: currentRefId.value,
  })
    .then((res) => {
      loading.value = false
      if (res?.success) {
        uiStatus.value = 'Cancelled'
        stopTimer()
        toast.success(__('Call cancelled'))
        autoCloseSoon()
      } else {
        toast.error(res?.message || __('Unable to cancel call right now'))
      }
    })
    .catch((err) => {
      loading.value = false
      toast.error(err?.message || __('Unable to cancel call right now'))
    })
}

function autoCloseSoon() {
  setTimeout(() => {
    showCallPopup.value = false
    showSmallCallPopup.value = false
  }, 1200)
}

/* -------------------------------------------------------
   Popup controls
------------------------------------------------------- */
function toggleCallPopup() {
  showCallPopup.value = !showCallPopup.value
  showSmallCallPopup.value = !showSmallCallPopup.value
}

function closePopupOnly() {
  showCallPopup.value = false
  showSmallCallPopup.value = false
}

/* -------------------------------------------------------
   Notes/Tasks
------------------------------------------------------- */
const note = ref({ name: '', title: '', content: '' })
const task = ref({
  name: '',
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  status: 'Open',
  priority: 'Medium',
})

function showNoteWindow() {
  showNoteModal.value = true
}
function showTaskWindow() {
  showTaskModal.value = true
}

async function updateNote(_note, insert_mode = false) {
  note.value = _note
  if (insert_mode && _note.name && currentRefId.value) {
    try {
      await call('crm.integrations.api.add_note_to_call_log', {
        call_sid: currentRefId.value,
        note: _note,
      })
      toast.success(__('Note added to call log'))
    } catch (e) {
      toast.error(__('Failed to add note'))
    }
  }
}

async function updateTask(_task, insert_mode = false) {
  task.value = _task
  if (insert_mode && _task.name && currentRefId.value) {
    try {
      await call('crm.integrations.api.add_task_to_call_log', {
        call_sid: currentRefId.value,
        task: _task,
      })
      toast.success(__('Task added to call log'))
    } catch (e) {
      toast.error(__('Failed to add task'))
    }
  }
}

/* -------------------------------------------------------
   Realtime updates from backend
------------------------------------------------------- */
function mapServerStatusToUI(status) {
  const s = String(status || '').toLowerCase()

  // handler.py saves doc.status as these values:
  if (s === 'initiated') return 'Calling...'
  if (s === 'ringing') return 'Ringing...'
  if (s === 'in progress') return 'In progress'
  if (s === 'completed') return 'Call ended'
  if (s === 'no answer') return 'No answer'
  if (s === 'failed') return 'Call failed'
  if (s === 'busy') return 'Busy'
  if (s === 'cancelled' || s === 'canceled') return 'Cancelled'

  return status || ''
}

function handleRealtime(data) {
  // data.ref_id is the unique_id used by handler (ref_id/call_id/uuid fallback)
  if (!data) return

  // Only update current call popup if it matches our current ref_id
  if (currentRefId.value && data.ref_id && data.ref_id !== currentRefId.value) {
    return
  }

  // capture call_id when webhook later sends it
  if (data.call_id && !providerCallId.value) {
    providerCallId.value = data.call_id
  }

  const newUi = mapServerStatusToUI(data.status)

  if (newUi) {
    // start timer when In progress starts
    if (newUi === 'In progress' && uiStatus.value !== 'In progress') {
      uiStatus.value = newUi
      startTimer()
      return
    }

    uiStatus.value = newUi
  }

  // stop timer and auto close on end states
  if (['Call ended', 'No answer', 'Call failed', 'Busy', 'Cancelled'].includes(uiStatus.value)) {
    stopTimer()
    autoCloseSoon()
  }
}

function setupRealtime() {
  if (window.$socket) {
    window.$socket.off('tata_tele_call') // prevent duplicate listeners
    window.$socket.on('tata_tele_call', (data) => {
      console.log('[TATA TELE REALTIME]', data)
      handleRealtime(data)
    })
  }
}

setupRealtime()

defineExpose({ makeOutgoingCall, setupRealtime, loading })
</script>

<style scoped>
/* optional */
</style>
