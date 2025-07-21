# 本地模型使用指南

## 概述

MDocAgent 现在支持使用本地模型，避免每次运行时从 Hugging Face 下载模型。

## 模型目录结构

```
MDocAgent/
├── models/
│   ├── colpaligemma-3b-mix-448-base/  # Image Retrieval 基础模型
│   ├── colpali/                       # Image Retrieval 适配器
│   ├── colbertv2.0/                   # Text Retrieval 模型
│   └── ...
```

## 支持的模型

### 1. Image Retrieval 模型
- **基础模型**: `colpaligemma-3b-mix-448-base`
  - 位置: `models/colpaligemma-3b-mix-448-base/`
  - 大小: 约 5.4GB
  - 用途: 多模态图像-文本理解

- **适配器模型**: `colpali`
  - 位置: `models/colpali/`
  - 大小: 约 75MB
  - 用途: 图像检索适配器

### 2. Text Retrieval 模型
- **ColBERT 模型**: `colbertv2.0`
  - 位置: `models/colbertv2.0/`
  - 用途: 文本检索

## 配置

模型路径配置在 `config/model_paths.yaml` 中：

```yaml
model_paths:
  colpaligemma_base: "models/colpaligemma-3b-mix-448-base"
  colpali_adapter: "models/colpali"
  colbert: "models/colbertv2.0"
```

## 使用方法

### 1. 测试模型路径

运行测试脚本验证模型是否正确配置：

```bash
python test_local_models.py
```

### 2. 运行检索

#### Image Retrieval
```bash
# 确保 config/base.yaml 中设置为 image 模式
python scripts/retrieve.py --config-name feta
```

#### Text Retrieval
```bash
# 修改 config/base.yaml 中设置为 text 模式
python scripts/retrieve.py --config-name feta
```

## 故障排除

### 1. 模型加载失败

如果本地模型加载失败，系统会自动回退到在线模型：

```
加载本地模型失败: [错误信息]
尝试使用在线模型...
```

### 2. 模型路径错误

检查模型目录是否存在：

```bash
ls -la models/
```

### 3. 权限问题

确保模型文件有读取权限：

```bash
chmod -R 644 models/
```

## 性能优化

### 1. 首次加载

首次加载本地模型可能需要一些时间，后续运行会更快。

### 2. 内存使用

- Image Retrieval 模型需要约 8GB GPU 内存
- Text Retrieval 模型需要约 4GB GPU 内存

### 3. 存储空间

确保有足够的存储空间：
- 总需求: 约 10GB
- 建议: 至少 15GB 可用空间

## 更新模型

如果需要更新模型，请：

1. 备份现有模型
2. 下载新模型到对应目录
3. 运行测试脚本验证
4. 更新配置文件（如需要）

## 注意事项

1. **模型完整性**: 确保模型文件完整，特别是 `.safetensors` 文件
2. **版本兼容性**: 确保模型版本与代码兼容
3. **网络备用**: 如果本地模型有问题，系统会自动使用在线模型
4. **缓存清理**: 如果遇到问题，可以清理 Python 缓存：`find . -name "__pycache__" -delete` 