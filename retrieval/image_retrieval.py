import torch
from torch.utils.data import DataLoader
from PIL import Image
from tqdm import tqdm
import os
import pickle
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from colpali_engine.models.paligemma_colbert_architecture import ColPali
from colpali_engine.trainer.retrieval_evaluator import CustomEvaluator
from colpali_engine.utils.colpali_processing_utils import process_images, process_queries
from transformers import AutoProcessor

from mydatasets.base_dataset import BaseDataset
from retrieval.base_retrieval import BaseRetrieval

# 导入模型路径工具
from utils.model_utils import get_model_path

class ColpaliRetrieval(BaseRetrieval):
    def __init__(self, config):
        self.config = config
        
        # 使用本地模型路径
        try:
            # 通过utils获取本地模型路径
            base_model_path = get_model_path('colpaligemma_base')
            adapter_model_path = get_model_path('colpali_adapter')
            
            print(f"正在加载基础模型: {base_model_path}")
            # 添加内存优化选项
            self.model = ColPali.from_pretrained(
                base_model_path, 
                torch_dtype=torch.float16,  # 使用 float16 减少内存使用
                device_map="cpu",           # 先加载到CPU，避免GPU内存问题
                low_cpu_mem_usage=True,     # 低 CPU 内存使用
            ).eval()
            
            # 如果GPU可用，尝试移动到GPU
            if torch.cuda.is_available():
                try:
                    print("尝试将模型移动到GPU...")
                    self.model = self.model.to("cuda")
                    print("模型已移动到GPU")
                except Exception as e:
                    print(f"GPU内存不足，保持在CPU: {e}")
            
            print(f"正在加载适配器: {adapter_model_path}")
            self.model.load_adapter(adapter_model_path)
            
            print(f"正在加载处理器: {adapter_model_path}")
            self.processor = AutoProcessor.from_pretrained(adapter_model_path)
            
        except Exception as e:
            print(f"加载本地模型失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print("回退到在线模型...")
            # 如果本地模型加载失败，回退到在线模型
            model_name = "vidore/colpali"
            self.model = ColPali.from_pretrained(
                "vidore/colpaligemma-3b-mix-448-base", 
                torch_dtype=torch.float16,  # 使用 float16 减少内存使用
                device_map="cpu",           # 先加载到CPU，避免GPU内存问题
                low_cpu_mem_usage=True,     # 低 CPU 内存使用
            ).eval()
            
            # 如果GPU可用，尝试移动到GPU
            if torch.cuda.is_available():
                try:
                    print("尝试将模型移动到GPU...")
                    self.model = self.model.to("cuda")
                    print("模型已移动到GPU")
                except Exception as e:
                    print(f"GPU内存不足，保持在CPU: {e}")
            self.model.load_adapter(model_name)
            self.processor = AutoProcessor.from_pretrained(model_name)
    
    def prepare(self, dataset: BaseDataset):
        os.makedirs(self.config.embed_dir, exist_ok=True)
        embed_path = self.config.embed_dir + "/" + dataset.config.name + "_embed.pkl"
        if os.path.exists(embed_path):
            with open(embed_path, "rb") as file:  # Use "rb" mode for binary reading
                document_embeds = pickle.load(file)
        else:
            document_embeds = {}
        
        samples = dataset.load_data(use_retreival=True)
        for sample in tqdm(samples):
            if sample[self.config.doc_key] in document_embeds:
                continue
            content_list = dataset.load_processed_content(sample, disable_load_image=False)
            images = [content.image for content in content_list]
            dataloader = DataLoader(
                images,
                batch_size=self.config.batch_size,
                shuffle=False,
                collate_fn=lambda x: process_images(self.processor, x).to(self.model.device),
            )
            image_embeds = []
            for batch_image in dataloader:
                with torch.no_grad():
                    batch_image = {k: v.to(self.model.device) for k, v in batch_image.items()}
                    batch_image_embed = self.model(**batch_image)
                    image_embeds.extend(batch_image_embed)
            try:
                document_embeds[sample[self.config.doc_key]] = torch.stack(image_embeds,axis=0)
            except:
                document_embeds[sample[self.config.doc_key]] = None
                print("Empty doc.")
        
        with open(embed_path, "wb") as f:
            pickle.dump(document_embeds, f)
            
        return document_embeds
            
    def find_sample_top_k(self, sample, document_embed, top_k: int, page_id_key: str):
        query = [sample[self.config.image_question_key]]
        batch_queries = process_queries(self.processor, query, Image.new("RGB", (448, 448), (255, 255, 255))).to(self.model.device)
        with torch.no_grad():    
            query_embed = self.model(**batch_queries)
        
        page_id_list = None
        if page_id_key in sample:
            page_id_list = sample[page_id_key]
            assert isinstance(page_id_list, list)
            
        retriever_evaluator = CustomEvaluator(is_multi_vector=True)
        scores = retriever_evaluator.evaluate(query_embed, document_embed)
        
        if page_id_list:
            scores_tensor = torch.tensor(scores)
            mask = torch.zeros_like(scores_tensor, dtype=torch.bool)
            for idx in page_id_list:
                mask[0, idx] = True
            masked_scores = torch.where(mask, scores_tensor, torch.full_like(scores_tensor, float('-inf')))
            top_page = torch.topk(masked_scores, min(top_k, len(page_id_list)), dim=-1)
        else:
            top_page = torch.topk(torch.tensor(scores), min(top_k,len(scores[0])), dim=-1)
            
        top_page_scores = top_page.values.tolist()[0] if top_page is not None else []
        top_page_indices = top_page.indices.tolist()[0] if top_page is not None else []
        
        return top_page_indices, top_page_scores
        
    def find_top_k(self, dataset: BaseDataset, force_prepare=False):
        document_embeds = self.load_document_embeds(dataset, force_prepare=force_prepare)
        top_k = self.config.top_k
        samples = dataset.load_data(use_retreival=True)
        for sample in tqdm(samples):
            if self.config.r_image_key in sample:
                continue
            document_embed = document_embeds[sample[self.config.doc_key]]
            top_page_indices, top_page_scores = self.find_sample_top_k(sample, document_embed, top_k, dataset.config.page_id_key)
            sample[self.config.r_image_key] = top_page_indices
            sample[self.config.r_image_key+"_score"] = top_page_scores
        path = dataset.dump_data(samples, use_retreival=True)
        print(f"Save retrieval results at {path}.")
        
    def load_document_embeds(self, dataset: BaseDataset, force_prepare=False):
        embed_path = self.config.embed_dir + "/" + dataset.config.name + "_embed.pkl"
        if os.path.exists(embed_path) and not force_prepare:
            with open(embed_path, "rb") as file:  # Use "rb" mode for binary reading
                document_embeds = pickle.load(file)
        else:
            document_embeds = self.prepare(dataset)
        return document_embeds