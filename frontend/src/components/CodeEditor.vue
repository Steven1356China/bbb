<template>
  <div class="code-editor">
    <div class="editor-header">
      <select v-model="language" @change="$emit('language-change', language)" class="language-select">
        <option value="cpp">C++</option>
        <option value="python">Python</option>
      </select>
      <div class="editor-actions">
        <button @click="$emit('run')" class="btn btn-primary mr-2">
          <i class="fas fa-play mr-1"></i>运行测试
        </button>
        <button @click="$emit('submit')" class="btn btn-success">
          <i class="fas fa-paper-plane mr-1"></i>提交
        </button>
      </div>
    </div>
    
    <div ref="editorContainer" class="editor-container"></div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as monaco from 'monaco-editor'
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker'
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker'
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'

self.MonacoEnvironment = {
  getWorker(_, label) {
    if (label === 'json') {
      return new jsonWorker()
    }
    if (label === 'css' || label === 'scss' || label === 'less') {
      return new cssWorker()
    }
    if (label === 'html' || label === 'handlebars' || label === 'razor') {
      return new htmlWorker()
    }
    if (label === 'typescript' || label === 'javascript') {
      return new tsWorker()
    }
    return new editorWorker()
  }
}

export default {
  name: 'CodeEditor',
  props: {
    value: {
      type: String,
      default: ''
    },
    initialLanguage: {
      type: String,
      default: 'cpp'
    }
  },
  emits: ['update:value', 'language-change', 'run', 'submit'],
  setup(props, { emit }) {
    const editorContainer = ref(null)
    const language = ref(props.initialLanguage)
    let editor = null
    
    const cppTemplate = `#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int main() {
    // 你的代码
    int n;
    cin >> n;
    
    // 示例：计算1到n的和
    long long sum = 0;
    for (int i = 1; i <= n; i++) {
        sum += i;
    }
    
    cout << sum << endl;
    return 0;
}`

    const pythonTemplate = `def solve():
    # 你的代码
    n = int(input())
    
    # 示例：计算1到n的和
    total = sum(range(1, n + 1))
    
    print(total)

if __name__ == "__main__":
    solve()`
    
    const initEditor = () => {
      if (!editorContainer.value) return
      
      // 获取对应语言的模板
      const template = language.value === 'cpp' ? cppTemplate : pythonTemplate
      const code = props.value || template
      
      editor = monaco.editor.create(editorContainer.value, {
        value: code,
        language: language.value === 'cpp' ? 'cpp' : 'python',
        theme: 'vs-dark',
        fontSize: 14,
        minimap: { enabled: true },
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        automaticLayout: true,
        tabSize: 2,
        insertSpaces: true
      })
      
      // 监听内容变化
      editor.onDidChangeModelContent(() => {
        emit('update:value', editor.getValue())
      })
    }
    
    const updateLanguage = () => {
      if (editor) {
        const newLanguage = language.value === 'cpp' ? 'cpp' : 'python'
        const model = editor.getModel()
        if (model) {
          monaco.editor.setModelLanguage(model, newLanguage)
        }
      }
    }
    
    onMounted(() => {
      initEditor()
    })
    
    onBeforeUnmount(() => {
      if (editor) {
        editor.dispose()
      }
    })
    
    watch(language, updateLanguage)
    
    return {
      editorContainer,
      language
    }
  }
}
</script>

<style scoped>
.code-editor {
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  overflow: hidden;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: #1e1e1e;
  border-bottom: 1px solid var(--border-color);
}

.language-select {
  background-color: #2d2d2d;
  color: white;
  border: 1px solid #404040;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.editor-actions {
  display: flex;
  align-items: center;
}

.editor-container {
  height: 500px;
}
</style>
