// stores/dashboard.js
import { defineStore } from 'pinia'
import api from '@/api/analysis.js';

const useCommentStore = defineStore('analysis', {
  state: () => ({
    // 分析状态
    isAnalyzing: false,
    //作文要求
    requirements: '',
    //作文内容
    essay: '',
    //作文字数
    words_count: 0,
    //年级
    grade: 0,
    //上传时间
    upload_time: '',
    // 实时反馈内容（六大点）- 直接存储显示的内容
    comment: '',
    // 分数总结JSON
    json_comment: null,
    // 最终结果（总分、各项得分、总评和六大点）
    finalResult: null,
    // 错误信息
    error: null,
    // 流控制
    streamPromise: null,
    // 节流控制
    chunkBuffer: [],     // 存储待处理的数据块
    rafId: null,         // requestAnimationFrame ID
    lastFlushTime: 0,    // 上次刷新时间
  }),
  
  actions: {
    // 批量更新内容 - 使用 requestAnimationFrame
    flushChunksWithRAF() {
      const now = performance.now();
      
      // 控制刷新频率：最多每16ms刷新一次（60fps）
      if (now - this.lastFlushTime < 16) {
        // 如果距离上次刷新不足16ms，继续等待
        this.rafId = requestAnimationFrame(() => this.flushChunksWithRAF());
        return;
      }
      
      if (this.chunkBuffer.length > 0) {
        // 计算本次应该处理多少条数据
        // 目标：每秒3000条，每帧(16ms)就是48条
        // 保守一点，每帧处理30-40条
        const targetPerFrame = 35;
        const batchSize = Math.min(targetPerFrame, this.chunkBuffer.length);
        
        // 取出要处理的数据块
        const batchContent = this.chunkBuffer.slice(0, batchSize).join('');
        
        // 更新 comment 和缓冲区
        this.$patch((state) => {
          state.comment += batchContent;
          state.chunkBuffer = state.chunkBuffer.slice(batchSize);
        });
         
        this.lastFlushTime = now;
        
        console.log(`🎯 RAF刷新: 处理 ${batchSize} 条, 剩余 ${this.chunkBuffer.length} 条`);
      }
      
      // 继续下一帧的刷新
      if (this.isAnalyzing) {
        this.rafId = requestAnimationFrame(() => this.flushChunksWithRAF());
      }
    },

    // 开始分析，并返回 Promise
    async startAnalysis(analysisText, isTest = false) {
      this.isAnalyzing = true;
      this.comment = '';  // 直接清空
      this.json_comment = null;
      this.finalResult = null;
      this.error = null;
      this.chunkBuffer = [];
      this.lastFlushTime = performance.now();
      
      // 清除之前的 RAF
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = null;
      }
      
      // 启动 RAF 刷新循环
      this.rafId = requestAnimationFrame(() => this.flushChunksWithRAF());
      
      // 保存流式 Promise
      this.streamPromise = new Promise((resolve, reject) => {
        let msgCount = 0;
        let lastLogTime = Date.now();
        let byteCount = 0;  // 统计接收的字节数
        
        if (isTest) {
          this._runTestSimulation(resolve, reject, analysisText);
          return;
        }
        
        api.analyzeEssayStream(
          analysisText,
          // onProgress（实时进度回调）
          (progress) => {
            if (progress.event === 'message') {
              msgCount++;
              const chunk = progress.data.message || '';
              byteCount += chunk.length;
              
              // 改为每10条打印一次速度统计
              if (msgCount % 10 === 1) {  // 每10条打印一次
                const timeElapsed = (Date.now() - lastLogTime) / 1000;
                const speed = (byteCount / timeElapsed / 1024).toFixed(2);
                console.log(`📊 接收速度: ${msgCount}条, ${speed}KB/s, 缓冲区: ${this.chunkBuffer.length}条`);
                lastLogTime = Date.now();
                byteCount = 0;
              }
              
              // 直接存入缓冲区
              this.$patch((state) => {
                state.chunkBuffer.push(chunk);
              });
              
              // 每100条打印一次日志
              if (msgCount % 100 === 0) {
                console.log(`📦 已接收 ${msgCount} 条消息, 缓冲区大小: ${this.chunkBuffer.length}`);
              }
            }
            else if (progress.event === 'sum_json') {
              this.json_comment = progress.data.message || null;
              console.log('📊 收到JSON数据:', this.json_comment);
            }
          },
          // onComplete（分析完成回调）
          (result) => {
            // 确保所有缓冲区内容都已显示
            const flushRemaining = () => {
              if (this.chunkBuffer.length > 0) {
                const remainingContent = this.chunkBuffer.join('');
                this.$patch((state) => {
                  state.comment += remainingContent;
                  state.chunkBuffer = [];
                });
                // 如果还有内容，继续下一帧处理
                this.rafId = requestAnimationFrame(flushRemaining);
              } else {
                // 所有内容处理完毕
                this.finalResult = result;
                this.isAnalyzing = false;
                
                if (this.rafId) {
                  cancelAnimationFrame(this.rafId);
                  this.rafId = null;
                }
                
                console.log('✅ 分析完成, 总消息数:', msgCount);
                resolve(result);
              }
            };
            
            flushRemaining();
          },
          // onError（分析失败回调）
          (err) => {
            this.error = err;
            this.isAnalyzing = false;
            
            if (this.rafId) {
              cancelAnimationFrame(this.rafId);
              this.rafId = null;
            }
            
            console.log('❌ 分析失败:', err);
            reject(err);
          }
        );
      });

      return this.streamPromise;
    },

    // 重置状态
    reset() {
      this.isAnalyzing = false;
      this.requirements = '';
      this.essay = '';
      this.words_count = 0;
      this.grade = 0;
      this.upload_time = '';
      this.comment = '';
      this.chunkBuffer = [];
      this.json_comment = null;
      this.finalResult = null;
      this.error = null;
      this.streamPromise = null;
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = null;
      }
    }
  }
});

export default useCommentStore;