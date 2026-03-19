import { ref } from 'vue';
const grades = ref([
    { value: 1, label: '一年级' },
    { value: 2, label: '二年级' },
    { value: 3, label: '三年级' },
    { value: 4, label: '四年级' },
    { value: 5, label: '五年级' },
    { value: 6, label: '六年级' },
    { value: 7, label: '七年级' },
    { value: 8, label: '八年级' },
    { value: 9, label: '九年级' },
    { value: 7, label: '初一' },
    { value: 8, label: '初二' },
    { value: 9, label: '初三' },
    { value: 10, label: '高一' },
    { value: 11, label: '高二' },
    { value: 12, label: '高三' },
  ])
const getGradeLabel = (value) => {
    if(!value) return ''
    const grade = grades.value.find(g => g.value === value)
    return grade ? grade.label : ''

}
export default getGradeLabel;