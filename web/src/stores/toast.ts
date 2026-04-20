import { reactive } from "vue";

interface ToastState {
  visible: boolean;
  message: string;
  isError: boolean;
}

const state = reactive<ToastState>({ visible: false, message: "", isError: false });
let timer: number | undefined;

export function useToast() {
  return {
    state,
    show(message: string, isError = false) {
      state.message = message;
      state.isError = isError;
      state.visible = true;
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        state.visible = false;
      }, 2800);
    },
  };
}
