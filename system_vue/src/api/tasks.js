// api/classes.js
import path from './path.js';
import instance from '../utils/request.js';

const api={
    async createTask(data){
        const res= await instance.post(path.taskUrl+'/tasks',{
            class_id: data.class_id,
            requirement: data.requirement
        });
        return res;
    },
    async getTaskDetail(taskId) {
        try {
            const res = await instance.get(path.taskUrl + `/tasks/${taskId}`);
            return res;
        } catch (error) {
            console.error('获取题目详情失败:', error);
            throw error;
        }
    },
    async getEssays(taskId) {
        try {
            const res = await instance.get(path.taskUrl + `/tasks/${taskId}/essays`);
            return res;
        } catch (error) {
            console.error('获取作文批改记录失败:', error);
            throw error;
        }
    },
    async deleteTask(taskId) {
        try {
            const res = await instance.delete(path.taskUrl + `/tasks/${taskId}`);
            return res;
        } catch (error) {
            console.error('删除题目失败:', error);
            throw error;
        }
    },
    async rejectEssay(essayId) {
        const res = await instance.post(path.taskUrl + `/essays/${essayId}/reject`);
        return res;
    }
}
export default api;