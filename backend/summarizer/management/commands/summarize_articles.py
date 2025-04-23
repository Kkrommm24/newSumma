import uuid
from django.core.management.base import BaseCommand
from summarizer.summarizers.llama.tasks import generate_article_summaries
import logging
import time
import torch
import subprocess

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tạo tóm tắt cho các bài viết chưa có'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=10, help='Số lượng bài viết cần tóm tắt')
        parser.add_argument('--verbose', action='store_true', help='Hiển thị log chi tiết')
        parser.add_argument('--check-gpu', action='store_true', help='Kiểm tra GPU trước khi chạy')

    def handle(self, *args, **options):
        limit = options.get('limit', 10)
        verbose = options.get('verbose', False)
        check_gpu = options.get('check_gpu', False)
        
        if check_gpu:
            self._check_gpu_status()
            return
            
        if verbose:
            for handler in logging.getLogger('news').handlers:
                handler.setLevel(logging.DEBUG)
            self.stdout.write("Chế độ verbose: BẬT")
        else:
            for handler in logging.getLogger('news').handlers:
                handler.setLevel(logging.INFO)
        
        start_time = time.time()
        
        try:
            count = generate_article_summaries(limit)
            if verbose:
                total_time = time.time() - start_time
                self.stdout.write(f"Tổng thời gian thực thi: {total_time:.2f} giây")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Lỗi: {str(e)}"))
    
    def _check_gpu_status(self):
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS("KIỂM TRA TRẠNG THÁI GPU"))
        self.stdout.write("=" * 50)
        
        # PyTorch info
        self.stdout.write("\nThông tin PyTorch:")
        self.stdout.write(f"PyTorch version: {torch.__version__}")
        self.stdout.write(f"CUDA available: {torch.cuda.is_available()}")
        if hasattr(torch.version, 'cuda'):
            self.stdout.write(f"CUDA version: {torch.version.cuda}")
        
        # NVIDIA-SMI
        self.stdout.write("\nThông tin NVIDIA-SMI:")
        try:
            result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, text=True)
            self.stdout.write(result.stdout)
        except FileNotFoundError:
            self.stdout.write("nvidia-smi không được cài đặt hoặc không tìm thấy")
        
        # NVCC version
        self.stdout.write("\nThông tin NVCC:")
        try:
            result = subprocess.run(['nvcc', '--version'], stdout=subprocess.PIPE, text=True)
            self.stdout.write(result.stdout)
        except FileNotFoundError:
            self.stdout.write("nvcc không được cài đặt hoặc không tìm thấy")
        
        self.stdout.write("\n" + "=" * 50)