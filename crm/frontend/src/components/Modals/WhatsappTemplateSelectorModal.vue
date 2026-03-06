<template>
  <Dialog
    v-model="show"
    :options="{ title: selectedTemplate ? __('Send Template') : __('WhatsApp Templates'), size: '4xl' }"
  >
    <template #body-content>
      <!-- Template List View -->
      <div v-if="!selectedTemplate">
        <div class="flex items-center justify-between mb-3">
          <TextInput
            ref="searchInput"
            v-model="search"
            type="text"
            :placeholder="__('Search templates...')"
            class="flex-1"
          >
            <template #prefix>
              <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" />
            </template>
          </TextInput>
          <div class="flex items-center gap-2 ml-2">
            <Button
              :label="syncing ? __('Syncing...') : __('Sync from Interakt')"
              :disabled="syncing"
              :loading="syncing"
              variant="subtle"
              theme="blue"
              @click="syncTemplates"
            >
              <template #prefix>
                <FeatherIcon name="refresh-cw" class="h-4 w-4" :class="{ 'animate-spin': syncing }" />
              </template>
            </Button>
          </div>
        </div>

        <!-- Sync result banner -->
        <div
          v-if="syncMessage"
          class="flex items-center gap-2 px-3 py-2 mb-3 rounded-md text-sm"
          :class="syncSuccess ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'"
        >
          <FeatherIcon :name="syncSuccess ? 'check-circle' : 'alert-circle'" class="h-4 w-4 shrink-0" />
          <span>{{ syncMessage }}</span>
        </div>

        <!-- Templates grid -->
        <div
          v-if="filteredTemplates.length"
          class="mt-1 grid max-h-[560px] grid-cols-1 gap-2.5 overflow-y-auto sm:grid-cols-2 lg:grid-cols-3"
        >
          <div
            v-for="template in filteredTemplates"
            :key="template.name"
            class="flex h-60 cursor-pointer flex-col rounded-lg border p-3.5 transition-all duration-150 hover:border-blue-300 hover:bg-blue-50/30 hover:shadow-sm"
            @click="selectTemplate(template)"
          >
            <!-- Template header -->
            <div class="border-b pb-2 mb-2">
              <div class="text-sm font-semibold text-ink-gray-9 truncate" :title="template.template_name || template.name">
                {{ template.template_name || template.name }}
              </div>
              <div class="mt-1.5 flex flex-wrap gap-1.5">
                <span
                  v-if="template.language_code"
                  class="inline-flex items-center rounded-full bg-surface-gray-2 px-2 py-0.5 text-[10px] font-medium text-ink-gray-5 uppercase"
                >
                  {{ template.language_code }}
                </span>
                <span
                  v-if="template.category"
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase"
                  :class="categoryColor(template.category)"
                >
                  {{ template.category }}
                </span>
                <span
                  v-if="template.status"
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase"
                  :class="statusColor(template.status)"
                >
                  {{ template.status }}
                </span>
              </div>
            </div>
            <!-- Template body preview -->
            <div class="flex-1 overflow-hidden text-xs text-ink-gray-5 leading-relaxed whitespace-pre-wrap">
              {{ truncateBody(template.body_text || template.template || '') }}
            </div>
            <!-- Template footer -->
            <div v-if="template.footer" class="mt-2 pt-1.5 border-t text-[10px] text-ink-gray-4 truncate">
              {{ template.footer }}
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="mt-2">
          <div class="flex h-56 flex-col items-center justify-center">
            <FeatherIcon name="message-circle" class="h-10 w-10 text-ink-gray-3 mb-3" />
            <div class="text-lg text-ink-gray-4">
              {{ __('No templates found') }}
            </div>
            <div class="mt-2 text-sm text-ink-gray-5 text-center max-w-md">
              {{ __('Click "Sync from Interakt" to fetch your WhatsApp templates.') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Variable Input Form -->
      <div v-else>
        <div class="mb-4">
          <Button variant="ghost" @click="selectedTemplate = null" class="mb-3">
            <template #prefix>
              <FeatherIcon name="arrow-left" class="h-4 w-4" />
            </template>
            {{ __('Back to templates') }}
          </Button>

          <!-- Template info card -->
          <div class="rounded-lg border bg-surface-gray-1 p-4 mb-4">
            <div class="flex items-start justify-between">
              <div>
                <div class="text-base font-semibold text-ink-gray-9">
                  {{ selectedTemplate.template_name || selectedTemplate.name }}
                </div>
                <div class="mt-1.5 flex gap-2">
                  <span
                    v-if="selectedTemplate.language_code"
                    class="inline-flex items-center rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-ink-gray-5 uppercase border"
                  >
                    {{ selectedTemplate.language_code }}
                  </span>
                  <span
                    v-if="selectedTemplate.category"
                    class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase"
                    :class="categoryColor(selectedTemplate.category)"
                  >
                    {{ selectedTemplate.category }}
                  </span>
                </div>
              </div>
            </div>
            <div class="mt-3 text-sm text-ink-gray-6 whitespace-pre-wrap leading-relaxed border-t pt-3">
              {{ selectedTemplate.body_text || selectedTemplate.template || '' }}
            </div>
            <div v-if="selectedTemplate.footer" class="mt-2 text-xs text-ink-gray-4 italic">
              {{ selectedTemplate.footer }}
            </div>
          </div>

          <!-- Header value input (for media templates) -->
          <div
            v-if="selectedTemplate.header_format && ['IMAGE', 'DOCUMENT', 'VIDEO'].includes(selectedTemplate.header_format)"
            class="mb-4"
          >
            <div class="text-sm font-medium text-ink-gray-8 mb-2">
              {{ __('Header') }} ({{ selectedTemplate.header_format }})
            </div>
            <TextInput
              v-model="headerValue"
              type="text"
              :placeholder="__('Enter media URL for {0} header', [selectedTemplate.header_format.toLowerCase()])"
            />
            <div
              v-if="selectedTemplate.header_format === 'DOCUMENT'"
              class="mt-2"
            >
              <TextInput
                v-model="headerFileName"
                type="text"
                :placeholder="__('File name (e.g., Invoice.pdf)')"
              />
            </div>
          </div>

          <!-- Header text variable input -->
          <div
            v-if="selectedTemplate.header_format === 'TEXT' && selectedTemplate.header_text && selectedTemplate.header_text.includes('{{')"
            class="mb-4"
          >
            <div class="text-sm font-medium text-ink-gray-8 mb-2">
              {{ __('Header Variable') }}
            </div>
            <TextInput
              v-model="headerValue"
              type="text"
              :placeholder="__('Value for header variable')"
            />
          </div>

          <!-- Body variable inputs -->
          <div v-if="bodyVariables.length" class="mb-4">
            <div class="text-sm font-medium text-ink-gray-8 mb-3">
              {{ __('Template Variables') }}
            </div>
            <div class="space-y-3">
              <div v-for="(variable, idx) in bodyVariables" :key="idx">
                <label class="block text-xs font-medium text-ink-gray-6 mb-1">
                  {{ variable.label }}
                </label>
                <TextInput
                  v-model="variable.value"
                  type="text"
                  :placeholder="variable.placeholder"
                />
              </div>
            </div>
          </div>

          <!-- Button variable inputs -->
          <div v-if="buttonVariables.length" class="mb-4">
            <div class="text-sm font-medium text-ink-gray-8 mb-3">
              {{ __('Button Variables') }}
            </div>
            <div class="space-y-3">
              <div v-for="(btn, idx) in buttonVariables" :key="idx">
                <label class="block text-xs font-medium text-ink-gray-6 mb-1">
                  {{ btn.label }}
                </label>
                <TextInput
                  v-model="btn.value"
                  type="text"
                  :placeholder="btn.placeholder"
                />
              </div>
            </div>
          </div>

          <!-- No variables notice -->
          <div
            v-if="!bodyVariables.length && !buttonVariables.length && !(selectedTemplate.header_format && ['IMAGE', 'DOCUMENT', 'VIDEO', 'TEXT'].includes(selectedTemplate.header_format))"
            class="mb-4 flex items-center gap-2 px-3 py-2 rounded-md bg-blue-50 border border-blue-200 text-blue-700 text-sm"
          >
            <FeatherIcon name="info" class="h-4 w-4 shrink-0" />
            <span>{{ __('This template has no variables. It will be sent as-is.') }}</span>
          </div>

          <!-- Send button -->
          <div class="flex justify-end gap-2 mt-4">
            <Button
              variant="subtle"
              :label="__('Cancel')"
              @click="selectedTemplate = null"
            />
            <Button
              variant="solid"
              theme="blue"
              :label="sending ? __('Sending...') : __('Send Template')"
              :disabled="sending"
              :loading="sending"
              @click="sendSelectedTemplate"
            >
              <template #prefix>
                <FeatherIcon name="send" class="h-4 w-4" />
              </template>
            </Button>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { createListResource, call, toast } from 'frappe-ui'
import { ref, computed, nextTick, watch, onMounted } from 'vue'

const props = defineProps({
  doctype: String,
  docname: String,
  phoneNumber: String,
})

const show = defineModel()

const emit = defineEmits(['send'])

const searchInput = ref('')
const search = ref('')
const syncing = ref(false)
const syncMessage = ref('')
const syncSuccess = ref(false)
const selectedTemplate = ref(null)
const headerValue = ref('')
const headerFileName = ref('')
const sending = ref(false)

// Load templates from local DB
const templates = createListResource({
  type: 'list',
  doctype: 'WhatsApp Templates',
  cache: ['whatsappTemplates'],
  fields: [
    'name', 'template_name', 'template', 'footer', 'language_code',
    'category', 'status', 'body_text', 'buttons', 'header_format',
    'header_type', 'header_text', 'variable_count', 'interakt_template_id',
  ],
  filters: {
    status: ['in', ['APPROVED', 'Active']],
  },
  orderBy: 'modified desc',
  pageLength: 99999,
})

onMounted(() => {
  if (templates.data == null) {
    templates.fetch()
  }
})

// Filtered templates based on search
const filteredTemplates = computed(() => {
  return (
    templates.data?.filter((template) => {
      const name = (template.template_name || template.name || '').toLowerCase()
      const body = (template.body_text || template.template || '').toLowerCase()
      const q = search.value.toLowerCase()
      return name.includes(q) || body.includes(q)
    }) ?? []
  )
})

// Parse body variables {{1}}, {{2}}, etc.
const bodyVariables = computed(() => {
  if (!selectedTemplate.value) return []
  const body = selectedTemplate.value.body_text || selectedTemplate.value.template || ''
  const matches = body.match(/\{\{(\d+)\}\}/g)
  if (!matches) return []

  const uniqueVars = [...new Set(matches)]
  return uniqueVars
    .map((m) => {
      const num = m.replace(/[{}]/g, '')
      return {
        index: parseInt(num),
        label: `Variable {{${num}}}`,
        placeholder: `Enter value for {{${num}}}`,
        value: '',
      }
    })
    .sort((a, b) => a.index - b.index)
})

// Parse button variables from buttons JSON
const buttonVariables = computed(() => {
  if (!selectedTemplate.value) return []
  const buttonsRaw = selectedTemplate.value.buttons
  if (!buttonsRaw) return []

  try {
    let buttons = typeof buttonsRaw === 'string' ? JSON.parse(buttonsRaw) : buttonsRaw
    if (typeof buttons === 'string') buttons = JSON.parse(buttons)

    const vars = []
    buttons.forEach((btn, idx) => {
      if (btn.type === 'URL' && btn.url && btn.url.includes('{{')) {
        vars.push({
          buttonIndex: idx,
          label: `Button "${btn.text}" — Dynamic URL variable`,
          placeholder: 'Enter dynamic URL value',
          value: '',
        })
      }
    })
    return vars
  } catch {
    return []
  }
})

function selectTemplate(template) {
  selectedTemplate.value = template
  headerValue.value = ''
  headerFileName.value = ''
}

function truncateBody(text) {
  if (!text) return ''
  return text.length > 200 ? text.substring(0, 200) + '...' : text
}

function categoryColor(category) {
  const colors = {
    MARKETING: 'bg-purple-50 text-purple-700',
    UTILITY: 'bg-blue-50 text-blue-700',
    AUTHENTICATION: 'bg-orange-50 text-orange-700',
  }
  return colors[category] || 'bg-surface-gray-2 text-ink-gray-5'
}

function statusColor(status) {
  const colors = {
    APPROVED: 'bg-green-50 text-green-700',
    Active: 'bg-green-50 text-green-700',
    PENDING: 'bg-yellow-50 text-yellow-700',
    REJECTED: 'bg-red-50 text-red-700',
    Inactive: 'bg-surface-gray-2 text-ink-gray-5',
  }
  return colors[status] || 'bg-surface-gray-2 text-ink-gray-5'
}

async function syncTemplates() {
  syncing.value = true
  syncMessage.value = ''
  try {
    const result = await call(
      'crm.integrations.interakt.api.sync_interakt_templates'
    )
    if (result.success) {
      syncSuccess.value = true
      syncMessage.value = `Synced ${result.synced} of ${result.total} templates successfully.`
      if (result.errors?.length) {
        syncMessage.value += ` (${result.errors.length} errors)`
      }
      templates.reload()
    } else {
      syncSuccess.value = false
      syncMessage.value = result.error || 'Failed to sync templates'
    }
  } catch (e) {
    syncSuccess.value = false
    syncMessage.value = e.message || 'Failed to sync templates'
  } finally {
    syncing.value = false
  }
}

async function sendSelectedTemplate() {
  if (!selectedTemplate.value) return
  sending.value = true

  try {
    const tpl = selectedTemplate.value
    const templateName = tpl.template_name || tpl.name
    const languageCode = tpl.language_code || 'en'

    // Build body_values array
    const bodyVals = bodyVariables.value.length
      ? bodyVariables.value.map((v) => v.value)
      : null

    // Build header_values
    let headerVals = null
    if (headerValue.value) {
      headerVals = [headerValue.value]
    }

    // Build button_values
    let buttonVals = null
    if (buttonVariables.value.length) {
      buttonVals = {}
      buttonVariables.value.forEach((btn) => {
        buttonVals[String(btn.buttonIndex)] = [btn.value]
      })
    }

    // Emit to parent with all template data
    emit('send', {
      template_name: templateName,
      language_code: languageCode,
      header_values: headerVals,
      body_values: bodyVals,
      button_values: buttonVals,
      file_name: headerFileName.value || null,
    })

    toast.success(__('Template "{0}" is being sent', [templateName]))

    show.value = false
    selectedTemplate.value = null
  } catch (e) {
    toast.error(e.message || __('Failed to send template'))
  } finally {
    sending.value = false
  }
}

watch(show, (value) => {
  if (value) {
    nextTick(() => searchInput.value?.el?.focus())
    selectedTemplate.value = null
    syncMessage.value = ''
  }
})
</script>
