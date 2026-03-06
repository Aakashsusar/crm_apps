<template>
  <TwilioCallUI ref="twilio" />
  <ExotelCallUI ref="exotel" />
  <TataCallUI ref="tata" />
  <Dialog
    v-model="show"
    :options="{
      title: __('Make call'),
      actions: [
        {
          label: __('Call using {0}', [callMedium]),
          variant: 'solid',
          onClick: makeCallUsing,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          type="text"
          v-model="mobileNumber"
          :label="__('Mobile Number')"
        />
        <FormControl
          type="select"
          v-model="callMedium"
          :label="__('Calling Medium')"
          :options="callingMediumOptions"
        />
        <div class="flex flex-col gap-1">
          <FormControl
            type="checkbox"
            v-model="isDefaultMedium"
            :label="__('Make {0} as default calling medium', [callMedium])"
          />

          <div v-if="isDefaultMedium" class="text-sm text-ink-gray-4">
            {{
              __('You can change the default calling medium from the settings')
            }}
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import TwilioCallUI from '@/components/Telephony/TwilioCallUI.vue'
import ExotelCallUI from '@/components/Telephony/ExotelCallUI.vue'
import TataCallUI from '@/components/Telephony/TataCallUI.vue'
import {
  twilioEnabled,
  exotelEnabled,
  tataEnabled,
  defaultCallingMedium,
} from '@/composables/settings'
import { globalStore } from '@/stores/global'
import { FormControl, call, toast } from 'frappe-ui'
import { computed, nextTick, ref, watch, onMounted } from 'vue'

const store = globalStore()

const twilio = ref(null)
const exotel = ref(null)
const tata = ref(null)

const loading = computed(() => {
  return (
    twilio.value?.loading || exotel.value?.loading || tata.value?.loading || false
  )
})

watch(loading, (value) => {
  store.callLoading = value
})

const callMedium = ref('Twilio')
const isDefaultMedium = ref(false)

const show = ref(false)
const mobileNumber = ref('')

const callingMediumOptions = computed(() => {
  const options = []
  if (twilioEnabled.value) options.push('Twilio')
  if (exotelEnabled.value) options.push('Exotel')
  if (tataEnabled.value) options.push('Tata Tele')
  return options.length > 0 ? options : ['Twilio', 'Exotel']
})

function makeCall(number) {
  console.log("=" .repeat(80))
  console.log("[CALL UI] Make Call Function Called")
  console.log("[CALL UI] Input Number:", number)
  console.log("[CALL UI] Twilio Enabled:", twilioEnabled.value)
  console.log("[CALL UI] Exotel Enabled:", exotelEnabled.value)
  console.log("[CALL UI] Tata Tele Enabled:", tataEnabled.value)
  console.log("[CALL UI] Default Calling Medium:", defaultCallingMedium.value)
  
  const enabledCount = [twilioEnabled.value, exotelEnabled.value, tataEnabled.value].filter(Boolean).length
  console.log("[CALL UI] Enabled Count:", enabledCount)
  
  if (enabledCount > 1 && !defaultCallingMedium.value) {
    console.log("[CALL UI] Multiple mediums enabled, showing dialog")
    mobileNumber.value = number
    show.value = true
    return
  }

  // Set default medium based on availability
  if (twilioEnabled.value) {
    callMedium.value = 'Twilio'
  } else if (exotelEnabled.value) {
    callMedium.value = 'Exotel'
  } else if (tataEnabled.value) {
    callMedium.value = 'Tata Tele'
  }
  
  if (defaultCallingMedium.value) {
    callMedium.value = defaultCallingMedium.value
  }

  console.log("[CALL UI] Call Medium Selected:", callMedium.value)
  mobileNumber.value = number
  console.log("[CALL UI] Mobile Number Set:", mobileNumber.value)
  console.log("[CALL UI] Calling makeCallUsing()...")
  makeCallUsing()
}

function makeCallUsing() {
  if (isDefaultMedium.value && callMedium.value) {
    setDefaultCallingMedium()
  }

  if (callMedium.value === 'Twilio') {
    twilio.value.makeOutgoingCall(mobileNumber.value)
  }

  if (callMedium.value === 'Exotel') {
    exotel.value.makeOutgoingCall(mobileNumber.value)
  }

  if (callMedium.value === 'Tata Tele') {
    tata.value.makeOutgoingCall(mobileNumber.value)
  }
  show.value = false
}

async function setDefaultCallingMedium() {
  await call('crm.integrations.api.set_default_calling_medium', {
    medium: callMedium.value,
  })

  defaultCallingMedium.value = callMedium.value
  toast.success(
    __('Default calling medium set successfully to {0}', [callMedium.value]),
  )
}

watch(
  [twilioEnabled, exotelEnabled, tataEnabled],
  ([twilioValue, exotelValue, tataValue]) => {
    console.log('[CALL UI] Watch triggered - Twilio:', twilioValue, 'Exotel:', exotelValue, 'Tata:', tataValue)
    
    nextTick(() => {
      console.log('[CALL UI] In nextTick, setting up telephony...')
      
      if (twilioValue) {
        console.log('[CALL UI] Setting up Twilio')
        twilio.value.setup()
        callMedium.value = 'Twilio'
      }

      if (exotelValue) {
        console.log('[CALL UI] Setting up Exotel')
        exotel.value.setup()
        callMedium.value = 'Exotel'
      }

      if (tataValue) {
        console.log('[CALL UI] Setting up Tata Tele')
        tata.value.setup()
        callMedium.value = 'Tata Tele'
      }

      if (twilioValue || exotelValue || tataValue) {
        console.log('[CALL UI] Registering makeCall function with global store')
        console.log('[CALL UI] makeCall function type:', typeof makeCall)
        store.setMakeCall(makeCall)
        console.log('[CALL UI] makeCall registered successfully')
      } else {
        console.warn('[CALL UI] No telephony service enabled!')
      }
    })
  },
  { immediate: true },
)

// Fallback: Register makeCall on mount to ensure it's always available
onMounted(() => {
  console.log('[CALL UI] Component mounted')
  console.log('[CALL UI] Registering makeCall as fallback')
  store.setMakeCall(makeCall)
})

defineExpose({
  loading,
})
</script>
