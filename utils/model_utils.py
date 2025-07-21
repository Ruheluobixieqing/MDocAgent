import os
from typing import Optional

# 尝试导入yaml，如果失败则使用简单的字符串解析
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("警告: pyyaml未安装，将使用简单的配置文件解析")

def get_model_path(model_name: str) -> str:
    """
    从配置文件获取模型路径
    
    Args:
        model_name: 模型名称
        
    Returns:
        模型路径
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 读取模型路径配置文件
    config_path = os.path.join(project_root, "config", "model_paths.yaml")
    
    try:
        if YAML_AVAILABLE:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            model_paths = config.get('model_paths', {})
        else:
            # 简单的配置文件解析
            model_paths = {}
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                in_model_paths = False
                for line in lines:
                    line = line.strip()
                    if line == 'model_paths:':
                        in_model_paths = True
                        continue
                    if in_model_paths and line.startswith('  ') and ':' in line:
                        if not line.startswith('  #'):  # 跳过注释
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"')
                            model_paths[key] = value
                    elif in_model_paths and line and not line.startswith('  '):
                        break
        
        if model_name not in model_paths:
            raise ValueError(f"模型 '{model_name}' 在配置文件中未找到")
        
        # 返回相对于项目根目录的完整路径
        relative_path = model_paths[model_name]
        full_path = os.path.join(project_root, relative_path)
        
        # 检查路径是否存在
        if not os.path.exists(full_path):
            print(f"警告: 模型路径不存在: {full_path}")
            
        return full_path
        
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件未找到: {config_path}")
    except Exception as e:
        if YAML_AVAILABLE and 'yaml' in str(e).lower():
            raise ValueError(f"配置文件格式错误: {e}")
        else:
            raise Exception(f"读取模型路径时出错: {e}")

def get_model_config(model_name: str) -> Optional[dict]:
    """
    获取模型配置信息
    
    Args:
        model_name: 模型名称
        
    Returns:
        模型配置字典，如果未找到则返回None
    """
    try:
        model_path = get_model_path(model_name)
        config_file = os.path.join(model_path, "config.json")
        
        if os.path.exists(config_file):
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except:
        return None 