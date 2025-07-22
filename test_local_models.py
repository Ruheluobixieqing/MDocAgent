#!/usr/bin/env python3
"""
测试本地模型加载的脚本
"""

import os
import sys
import torch
from pathlib import Path

def test_qwen2vl():
    """测试Qwen2VL模型"""
    print("=== 测试 Qwen2VL 模型 ===")
    
    try:
        from models.qwen import Qwen2VL
        
        model_path = "models/Qwen2-VL-7B-Instruct"
        if not os.path.exists(model_path):
            print(f"❌ 模型路径不存在: {model_path}")
            return False
            
        # 创建配置对象
        class Config:
            def __init__(self, model_id):
                self.model_id = model_id
                self.max_new_tokens = 512
        
        config = Config(model_path)
        print(f"正在加载模型: {model_path}")
        model = Qwen2VL(config)
        print("✅ Qwen2VL 模型加载成功")
        return True
        
    except Exception as e:
        print(f"❌ Qwen2VL 模型加载失败: {e}")
        return False

def test_opt27b():
    """测试OPT-2.7B模型"""
    print("\n=== 测试 OPT-2.7B 模型 ===")
    
    try:
        from models.llama import Llama3
        
        model_path = "models/opt-2.7b"
        if not os.path.exists(model_path):
            print(f"❌ 模型路径不存在: {model_path}")
            return False
            
        # 创建配置对象
        class Config:
            def __init__(self, model_id):
                self.model_id = model_id
                self.max_new_tokens = 512
        
        config = Config(model_path)
        print(f"正在加载模型: {model_path}")
        model = Llama3(config)
        print("✅ OPT-2.7B 模型加载成功")
        return True
        
    except Exception as e:
        print(f"❌ OPT-2.7B 模型加载失败: {e}")
        return False

def test_config_files():
    """测试配置文件"""
    print("\n=== 测试配置文件 ===")
    
    # 测试qwen2vl配置
    try:
        import yaml
        with open("config/model/qwen2vl.yaml", "r") as f:
            qwen_config = yaml.safe_load(f)
        print(f"✅ Qwen2VL 配置: {qwen_config.get('model_id')}")
    except Exception as e:
        print(f"❌ Qwen2VL 配置错误: {e}")
    
    # 测试llama31配置
    try:
        with open("config/model/llama31.yaml", "r") as f:
            llama_config = yaml.safe_load(f)
        print(f"✅ Llama31 配置: {llama_config.get('model_id')}")
    except Exception as e:
        print(f"❌ Llama31 配置错误: {e}")

def check_model_files():
    """检查模型文件"""
    print("\n=== 检查模型文件 ===")
    
    models_to_check = {
        "Qwen2VL": "models/Qwen2-VL-7B-Instruct",
        "OPT-2.7B": "models/opt-2.7b"
    }
    
    for name, path in models_to_check.items():
        if os.path.exists(path):
            print(f"✅ {name}: {path} (存在)")
            
            # 检查关键文件
            if name == "OPT-2.7B":
                # OPT模型使用不同的tokenizer文件
                key_files = ["config.json", "vocab.json", "tokenizer_config.json"]
            else:
                key_files = ["config.json", "tokenizer.json"]
                
            for file in key_files:
                file_path = os.path.join(path, file)
                if os.path.exists(file_path):
                    print(f"  ✅ {file}")
                else:
                    print(f"  ❌ {file} (缺失)")
        else:
            print(f"❌ {name}: {path} (不存在)")

if __name__ == "__main__":
    print("=== 本地模型测试工具 ===\n")
    
    # 检查模型文件
    check_model_files()
    
    # 测试配置文件
    test_config_files()
    
    # 测试模型加载
    qwen_success = test_qwen2vl()
    opt_success = test_opt27b()
    
    print("\n=== 测试结果 ===")
    if qwen_success and opt_success:
        print("🎉 所有模型测试通过！可以开始推理了")
        print("\n下一步:")
        print("python scripts/predict.py --config-name feta run-name=my_test_run")
    else:
        print("❌ 部分模型测试失败，请检查配置") 