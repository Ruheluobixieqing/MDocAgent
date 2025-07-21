#!/usr/bin/env python3
"""
修复AdamW导入问题的补丁
在导入colbert之前运行此脚本
"""

import sys
import os

# 添加torch.optim.AdamW到transformers模块
import torch.optim
import transformers

# 将AdamW添加到transformers模块中
if not hasattr(transformers, 'AdamW'):
    transformers.AdamW = torch.optim.AdamW

print("AdamW补丁已应用，现在可以从transformers导入AdamW了") 