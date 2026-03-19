// src/api/history.js
import path from './path.js';
import instance from '../utils/request.js';

const api = {
    // 获取用户的历史记录列表（分页）
    async getUserHistory(userId, params={}) {
        const res = await instance.get(path.baseUrl + `/history/${userId}`, {
            params: {
                page: params.page || 1,
                page_size: params.pageSize || 10,     
                // 只有当有值时，才添加这些参数
                ...(params.title ? { title: params.title } : {}),
                ...(params.start_date ? { start_date: params.start_date } : {}),
                ...(params.end_date ? { end_date: params.end_date } : {})
            }
        });
        return res;
    },

    // 获取单条历史记录的详细信息
    async getHistoryDetail(essayId) {
        const res = await instance.get(path.baseUrl + `/history/detail/${essayId}`);
        return res;
    },

    // 删除历史记录
    async deleteHistory(essayId) {
        const res = await instance.delete(path.baseUrl + `/history/${essayId}`);
        return res;
    },

    // 修改历史记录标题
    async updateHistoryTitle(essayId, title) {
        const res = await instance.put(path.baseUrl + `/history/${essayId}/title`, {
            title: title
        });
        return res;
    }
};

export default api;