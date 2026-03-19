// api/classes.js
import path from './path.js';
import instance from '../utils/request.js';

const api={
    async createClass(data){
        const res= await instance.post(path.baseUrl+'/classes',{
            class_name: data
        });
        return res;
    },
    async getClasses() {
        const res = await instance.get(path.baseUrl + '/classes');
        return res;
    },
    async editClass(classId, newName) {
        const res = await instance.put(path.baseUrl + `/classes/${classId}`, {
            class_name: newName
        });
        return res;
    },
    async deleteClass(classId) {
        const res = await instance.delete(path.baseUrl + `/classes/${classId}`);
        return res;
    },
    async getClassDetail(classId) {
        const res = await instance.get(path.baseUrl + `/classes/${classId}`);
        return res;
    },
    async getClassStudents(classId) {
        const res = await instance.get(path.baseUrl + `/classes/${classId}/students`);
        return res;
    }
}
export default api;