import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'

export const globalStore = defineStore('crm-global', () => {
  // Store references that will be set by the app (reactive so components pick up changes)
  const $dialog = shallowRef(null)
  const $socket = shallowRef(null)

  let callMethod = () => {
    console.warn('[Global Store] makeCall called but no call method has been set yet. Make sure CallUI component is mounted.')
  }
  const callLoading = ref(false)

  function setGlobalProperties(dialog, socket) {
    $dialog.value = dialog
    $socket.value = socket
    console.log('[Global Store] Global properties set - dialog:', typeof dialog, 'socket:', typeof socket)
  }

  function setMakeCall(value) {
    console.log('[Global Store] setMakeCall called with:', typeof value)
    if (typeof value !== 'function') {
      console.error('[Global Store] setMakeCall received non-function:', value)
      return
    }
    callMethod = value
    console.log('[Global Store] Call method registered successfully')
  }

  function makeCall(number) {
    console.log('[Global Store] makeCall invoked with number:', number)
    console.log('[Global Store] callMethod type:', typeof callMethod)

    if (callMethod.toString().includes('no call method has been set')) {
      console.error('[Global Store] Call method not registered! CallUI may not be mounted or settings not loaded.')
    }

    callMethod(number)
  }

  return {
    $dialog,
    $socket,
    setGlobalProperties,
    makeCall,
    setMakeCall,
    callLoading,
  }
})
