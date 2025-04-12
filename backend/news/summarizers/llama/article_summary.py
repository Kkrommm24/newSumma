import logging
import os
import json
from typing import Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from huggingface_hub import login
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tạo handler để hiển thị ra terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Tạo formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Thêm handler vào logger
logger.addHandler(console_handler)

SUMMARY_PROMPT = (
    "Bạn là một trợ lý tóm tắt văn bản. Hãy tóm tắt ngắn gọn và chính xác bài viết sau trong 150 chữ. "
    "Không đánh số, không đặt câu hỏi, chỉ nêu sự kiện chính. "
    "Bài viết: {content} "
    "Tóm tắt: "
)

class LlamaSummarizer:
    def __init__(self):
        self.hf_token = os.getenv('HF_TOKEN')
        if not self.hf_token:
            raise ValueError("HF_TOKEN không được tìm thấy trong biến môi trường")
        try:
            login(token=self.hf_token, write_permission=False)
        except Exception as e:
            logger.warning(f"Không thể đăng nhập với token: {str(e)}")
        
        self.model_path = os.getenv('LLAMA_MODEL_PATH')
        if not self.model_path or not os.path.exists(self.model_path):
            self.model_path = os.path.join(os.getcwd(), 'llama_finetune_model')
        
        if not os.path.exists(self.model_path):
            raise ValueError(f"Không tìm thấy thư mục model tại {self.model_path}")
        
        logger.info(f"Sử dụng model tại: {self.model_path}")

        self.max_input_length = 2048
        self.max_summary_length = 512
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Sử dụng device: {self.device}")
        if self.device == "cuda":
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        
        self._load_model()
    
    def _load_model(self):
        """
        Tải mô hình và tokenizer
        """
        try:
            adapter_config_path = os.path.join(self.model_path, 'adapter_config.json')
            if not os.path.exists(adapter_config_path):
                raise FileNotFoundError(f"Không tìm thấy adapter_config.json trong {self.model_path}")
            
            with open(adapter_config_path, 'r') as f:
                adapter_config = json.load(f)
                base_model_name = adapter_config.get('base_model_name_or_path')
                if not base_model_name:
                    raise ValueError("adapter_config.json không chứa base_model_name_or_path")
            
            # Tối ưu tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                base_model_name,
                padding_side="left",
                trust_remote_code=True,
                token=self.hf_token
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Tối ưu model loading
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                token=self.hf_token,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map={"": 0} if torch.cuda.is_available() else "auto",
                low_cpu_mem_usage=True
            )
            
            self.model = PeftModel.from_pretrained(
                base_model,
                self.model_path,
                is_trainable=False,
                local_files_only=True
            )
            
            self.model.resize_token_embeddings(len(self.tokenizer))
            
        except Exception as e:
            logger.exception(f"Lỗi khi tải mô hình: {str(e)}")
            raise
    
    def _clean_summary(self, summary: str) -> str:
        """Làm sạch summary bằng cách loại bỏ các phần không mong muốn"""
        # Loại bỏ các dòng đánh số
        summary = re.sub(r'^\d+\.\s*', '', summary, flags=re.MULTILINE)
        
        # Loại bỏ các câu hỏi
        summary = re.sub(r'[?].*$', '', summary, flags=re.MULTILINE)
        
        # Loại bỏ các marker không mong muốn
        unwanted_markers = [
            "### Lời giải:", "### Đáp án:", "### Giải thích:", 
            "Câu hỏi:", "Trả lời:", "Vấn đề:", "Giải pháp:",
            "Kết luận:", "Tóm lại:", "Tóm tắt:", "Bài viết:"
        ]
        for marker in unwanted_markers:
            if marker in summary:
                summary = summary.split(marker)[0].strip()
        
        # Loại bỏ khoảng trắng thừa
        summary = re.sub(r'\s+', ' ', summary)
        summary = summary.strip()
        
        return summary
    
    def summarize(self, content: str) -> Optional[str]:
        try:
            if not content or len(content.strip()) == 0:
                logger.error("Nội dung bài viết trống")
                return None

            content_preview = content[:100] + "..." if len(content) > 100 else content
            logger.info(f"Đang tóm tắt bài viết: {content_preview}")
            logger.info(f"Sử dụng device: {self.device}")
            if self.device == "cuda":
                logger.info(f"GPU memory đang sử dụng: {torch.cuda.memory_allocated(0)/1024**2:.2f}MB")

            prompt = SUMMARY_PROMPT.format(content=content)

            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                padding="max_length",
                truncation=True,
                max_length=self.max_input_length,
                add_special_tokens=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_new_tokens=self.max_summary_length,
                    min_new_tokens=50,
                    num_beams=5,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    length_penalty=1.0,
                )

            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            summary_start = generated_text.find("Tóm tắt:")
            if summary_start == -1:
                logger.error("Không tìm thấy marker 'Tóm tắt:' trong văn bản sinh ra")
                return None
                
            summary_start += len("Tóm tắt:")
            summary = generated_text[summary_start:].strip()
            
            # Làm sạch summary
            summary = self._clean_summary(summary)
            
            if not summary:
                logger.error("Summary trống sau khi làm sạch")
                return None
                
            logger.info(f"Tóm tắt thành công: {summary[:100]}...")
                
            return summary
            
        except Exception as e:
            logger.exception(f"Lỗi khi tóm tắt nội dung: {str(e)}")
            return None  
