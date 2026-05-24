# AI 知识库示例

## 机器学习简介

机器学习是人工智能的一个分支，它使计算机能够从数据中学习和改进，而无需进行明确的编程。

### 主要类型

1. **监督学习**：使用标记的训练数据来学习从输入到输出的映射。
2. **无监督学习**：使用未标记的数据来发现数据中的隐藏模式。
3. **强化学习**：通过与环境交互并根据奖励信号学习来做出决策。

### 常见算法

- 线性回归
- 决策树和随机森林
- 支持向量机（SVM）
- 神经网络和深度学习

## Python 数据处理基础

Python 是数据科学和机器学习中最流行的编程语言之一。

### 核心库

- **NumPy**：提供高效的数组运算和数学函数
- **Pandas**：提供 DataFrame 数据结构，用于数据清洗和分析
- **Matplotlib**：用于数据可视化的绘图库
- **Scikit-learn**：提供各种机器学习算法的实现

### 简单示例

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# 加载数据
data = pd.read_csv('data.csv')
X = data.drop('target', axis=1)
y = data['target']

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 训练模型
model = RandomForestClassifier()
model.fit(X_train, y_train)

# 评估
accuracy = model.score(X_test, y_test)
print(f'准确率: {accuracy}')
```

## 大语言模型（LLM）

大语言模型是近年来 AI 领域最重要的突破之一。

### 关键概念

- **Transformer 架构**：所有现代 LLM 的基础，基于自注意力机制
- **预训练 + 微调**：先在大量文本上预训练，再针对特定任务微调
- **上下文长度**：模型一次能处理的 token 数量
- **RAG（检索增强生成）**：结合检索和生成，让模型基于外部知识回答问题

### 常见模型

- GPT-4 / GPT-3.5（OpenAI）
- Claude（Anthropic）
- DeepSeek
- LLaMA（Meta）
- Qwen（阿里巴巴）
