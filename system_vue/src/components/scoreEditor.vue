<template>
  <div 
    class="max-score-editor" 
    :class="{ 'compact-mode': compact }"
    @mouseenter="showTooltip = true" 
    @mouseleave="showTooltip = false"
  >
    <!-- 悬浮提示 -->
    <div v-if="showTooltip" class="score-tooltip">
      <el-icon><Edit /></el-icon>
      <span>点击修改满分值</span>
    </div>
    
    <div class="max-score-input-wrapper">
      <el-input
        v-if="isEditing"
        ref="inputRef"
        v-model="editingValue"
        type="number"
        :min="min"
        :max="max"
        :step="step"
        :size="size"
        :placeholder="placeholder"
        @keyup.enter="confirmChange"
        @blur="confirmChange"
        @keyup.esc="cancelEditing"
      />
      <span v-else class="max-score-display" @click="startEditing">
        {{ displayValue }}分制
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Number,
    required: true
  },
  min: {
    type: Number,
    default: 1
  },
  max: {
    type: Number,
    default: 200
  },
  step: {
    type: Number,
    default: 1
  },
  size: {
    type: String,
    default: 'small'
  },
  placeholder: {
    type: String,
    default: '请输入'
  },
  compact: {
    type: Boolean,
    default: true
  },
  confirmTitle: {
    type: String,
    default: '确认修改'
  },
  confirmMessage: {
    type: Function,
    default: null
  },
  showConfirm: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'confirm'])

// 状态
const isEditing = ref(false)
const editingValue = ref('')
const inputRef = ref(null)
const showTooltip = ref(false)
const originalValue = ref(props.modelValue)// 保存原始值，用于取消时恢复

// 计算显示的值
const displayValue = computed(() => {
  return props.modelValue
})

// 开始编辑
const startEditing = () => {
  editingValue.value = props.modelValue
  originalValue.value = props.modelValue // 保存当前值作为原始值
  isEditing.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// 取消编辑
const cancelEditing = () => {
  isEditing.value = false
  editingValue.value = ''
  // 恢复到原始值
  if (originalValue.value !== props.modelValue) {
    // 如果需要，可以在这里触发一个事件来恢复值
    // 但通常不需要，因为 props.modelValue 没有变化
  }
}

// 验证输入
const validateInput = (value) => {
  const num = parseInt(value)
  if (isNaN(num) || num < props.min || num > props.max) {
    ElMessage.warning(`请输入${props.min}-${props.max}之间的有效数字`)
    return false
  }
  return num
}

// 确认变更
const confirmChange = async () => {
  const newValue = validateInput(editingValue.value)
  if (!newValue) {
    nextTick(() => {
      inputRef.value?.focus()
    })
    return
  }

  if (newValue === props.modelValue) {
    cancelEditing()
    return
  }

  if (props.showConfirm) {
    try {
      let message = `确定要将满分值从 ${props.modelValue} 改为 ${newValue} 吗？`
      if (props.confirmMessage) {
        message = props.confirmMessage(props.modelValue, newValue)
      }

      await ElMessageBox.confirm(
        message,
        props.confirmTitle,
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          width: '500px'
        }
      )

      handleChange(newValue)

    } catch (error) {
      if (error !== 'cancel') {
        console.error('确认修改失败:', error)
      }
      isEditing.value = false
      editingValue.value = ''
    }
  } else {
    handleChange(newValue)
  }
}

// 处理值变更
const handleChange = (newValue) => {
  emit('update:modelValue', newValue)
  emit('change', newValue)
  emit('confirm', newValue)
  
  isEditing.value = false
  ElMessage.success(`满分值已调整为 ${newValue}`)
}

defineExpose({
  startEditing,
  cancelEditing,
  isEditing
})
</script>

<style scoped>
.max-score-editor {
  position: relative;
  display: inline-block;
}

 /* .max-score-editor.compact-mode {
 紧凑模式样式 
}*/

.score-tooltip {
  position: absolute;
  top: -30px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.75);
  color: white;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 10;
  animation: fadeIn 0.2s ease;
}

.score-tooltip::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 4px solid rgba(0, 0, 0, 0.75);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.max-score-input-wrapper {
  min-width: 50px;
}

.max-score-display {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  background: #fee8e8e7;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: #ff7878;
  border: 1px solid #ffd9d9;
  transition: all 0.2s;
  white-space: nowrap;
  height: 14px;
  line-height: 14px;
}

.max-score-display:hover {
  background: #ffe5e1;
  border-color: #fe816b;
  transform: scale(1.05);
}

.max-score-input-wrapper :deep(.el-input__inner) {
  text-align: center;
  font-size: 14px;
  height: 28px;
  width: 70px;
  border-radius: 14px;
}
</style>