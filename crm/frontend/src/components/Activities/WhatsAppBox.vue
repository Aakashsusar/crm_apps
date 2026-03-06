<template>
  <!-- Reply preview bar -->
  <div
    v-if="reply?.message"
    class="flex items-center gap-2 px-3 py-1.5 mx-3 mb-1 sm:mx-10 rounded-md bg-surface-gray-2 border border-outline-gray-modals text-xs"
  >
    <div class="flex-1">
      <div class="font-medium text-ink-gray-6">
        {{ reply.type == 'Incoming' ? __('Replying to customer') : __('Replying to your message') }}
      </div>
      <div class="mt-0.5 line-clamp-1 text-ink-gray-5">
        {{ reply.message }}
      </div>
    </div>
    <FeatherIcon
      name="x"
      class="h-4 w-4 cursor-pointer text-ink-gray-5"
      @click="reply = {}"
    />
  </div>
  <!-- 24h Conversation Window Indicator -->
  <div
    v-if="!isWindowOpen"
    class="flex items-center gap-2 px-3 py-1.5 mx-3 mb-1 sm:mx-10 rounded-md bg-yellow-50 border border-yellow-200 text-yellow-700 text-xs"
  >
    <FeatherIcon name="alert-circle" class="h-3.5 w-3.5 shrink-0" />
    <span>{{ __('Conversation window closed — Only template messages can be sent') }}</span>
  </div>
  <div
    v-else
    class="flex items-center gap-2 px-3 py-1.5 mx-3 mb-1 sm:mx-10 rounded-md bg-green-50 border border-green-200 text-green-700 text-xs"
  >
    <FeatherIcon name="check-circle" class="h-3.5 w-3.5 shrink-0" />
    <span>{{ __('Conversation window open') }}</span>
  </div>
  <div class="flex items-end gap-2 px-3 py-2.5 sm:px-10" v-bind="$attrs">
    <div class="flex h-8 items-center gap-2">
      <FileUploader @success="(file) => uploadFile(file)">
        <template v-slot="{ openFileSelector }">
          <div class="flex items-center space-x-2">
            <Dropdown :options="uploadOptions(openFileSelector)">
              <FeatherIcon
                name="plus"
                class="size-4.5 cursor-pointer text-ink-gray-5"
              />
            </Dropdown>
          </div>
        </template>
      </FileUploader>
      <IconPicker
        v-model="emoji"
        v-slot="{ togglePopover }"
        @update:modelValue="
          () => {
            content += emoji
            $refs.textareaRef.el.focus()
            capture('whatsapp_emoji_added')
          }
        "
      >
        <SmileIcon
          @click="togglePopover"
          class="flex size-4.5 cursor-pointer rounded-sm text-xl leading-none text-ink-gray-4"
        />
      </IconPicker>
    </div>
    <Textarea
      ref="textareaRef"
      type="textarea"
      class="min-h-8 w-full"
      :rows="rows"
      v-model="content"
      :placeholder="isWindowOpen ? placeholder : __('Window closed. Use templates instead.')"
      :disabled="!isWindowOpen"
      @focus="rows = 6"
      @blur="rows = 1"
      @keydown.enter.stop="(e) => sendTextMessage(e)"
    />
  </div>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import SmileIcon from '@/components/Icons/SmileIcon.vue'
import { capture } from '@/telemetry'
import { createResource, Textarea, FileUploader, Dropdown } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'

const props = defineProps({
  doctype: String,
})

const doc = defineModel()
const whatsapp = defineModel('whatsapp')
const reply = defineModel('reply')
const rows = ref(1)
const textareaRef = ref(null)
const emoji = ref('')

const content = ref('')
const placeholder = ref(__('Type your message here...'))
const fileType = ref('')

// Compute conversation window status from messages
const isWindowOpen = computed(() => {
  const messages = whatsapp.value?.data
  if (!messages || !messages.length) return false

  // Find last incoming message
  const incomingMessages = messages.filter((m) => m.type === 'Incoming')
  if (!incomingMessages.length) return false

  const lastIncoming = incomingMessages[incomingMessages.length - 1]
  const lastIncomingTime = new Date(lastIncoming.creation)
  const now = new Date()
  const hoursDiff = (now - lastIncomingTime) / (1000 * 60 * 60)
  return hoursDiff < 24
})

function show() {
  nextTick(() => textareaRef.value.el.focus())
}

// Auto-focus when reply is selected
watch(() => reply.value, (value) => {
  if (value?.message) {
    show()
  }
})

function uploadFile(file) {
  whatsapp.value.attach = file.file_url
  whatsapp.value.content_type = fileType.value
  sendWhatsAppMessage()
  capture('whatsapp_upload_file')
}

function sendTextMessage(event) {
  if (event.shiftKey) return
  if (!isWindowOpen.value) return
  sendWhatsAppMessage()
  textareaRef.value.el?.blur()
  content.value = ''
  capture('whatsapp_send_message')
}

async function sendWhatsAppMessage() {
  let args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    message: content.value,
    to: doc.value.mobile_no,
    attach: whatsapp.value.attach || '',
    reply_to: reply.value?.name || '',
    content_type: whatsapp.value.content_type,
  }
  content.value = ''
  fileType.value = ''
  whatsapp.value.attach = ''
  whatsapp.value.content_type = 'text'
  reply.value = {}
  createResource({
    url: 'crm.api.whatsapp.create_whatsapp_message',
    params: args,
    auto: true,
  })
}

function uploadOptions(openFileSelector) {
  return [
    {
      label: __('Upload Document'),
      icon: 'file',
      onClick: () => {
        fileType.value = 'document'
        openFileSelector()
      },
    },
    {
      label: __('Upload Image'),
      icon: 'image',
      onClick: () => {
        fileType.value = 'image'
        openFileSelector('image/*')
      },
    },
    {
      label: __('Upload Video'),
      icon: 'video',
      onClick: () => {
        fileType.value = 'video'
        openFileSelector('video/*')
      },
    },
  ]
}

defineExpose({ show })
</script>
