<template>
  <div class="markdown-body" v-html="renderedContent"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps({
  content: {
    type: String,
    default: ''
  }
})

// 初始化 markdown-it
const md = new MarkdownIt({
  html: true,        // 允许 HTML 标签
  breaks: true,      // 转换换行符为 <br>
  linkify: true,     // 自动识别 URL 并转为链接
  typographer: true, // 启用一些语言中性的替换和引号美化
})

const renderedContent = computed(() => {
  return md.render(props.content || '')
})
</script>

<style>
/* 引入 GitHub 风格的 Markdown 样式，让界面更美观 */
@import 'https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown.min.css' screen and (min-width: 0);

.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
  padding: 10px 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #24292e;
  background-color: #ffffff;
  border-radius: 6px;
}

/* 针对你的深色背景或特定布局的调整 */
.markdown-body pre {
  background-color: #ffffff;
  border-radius: 6px;
  padding: 16px;
}

.markdown-body code {
  background-color: rgba(175, 184, 193, 0.2);
  border-radius: 6px;
  padding: 0.2em 0.4em;
  font-size: 85%;
}

/* 标题样式微调 */
.markdown-body h1, .markdown-body h2 {
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  font-weight: 600;
}
</style>