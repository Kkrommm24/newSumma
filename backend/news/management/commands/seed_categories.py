from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import Category


class Command(BaseCommand):
    help = 'Seed predefined categories into the database'

    def handle(self, *args, **options):
        CATEGORY_DATA = {
            "thoi-su": "THỜI SỰ",
            "kinh-doanh": "KINH DOANH",
            "goc-nhin": "GÓC NHÌN",
            "bat-dong-san": "BẤT ĐỘNG SẢN",
            "suces": "SỨC KHOẺ",
            "xe": "XE",
            "du-lich": "DU LỊCH",
            "y-kien": "Ý KIẾN",
            "bong-da": "BÓNG ĐÁ",
            "the-gioi": "THẾ GIỚI",
            "kinh-te": "KINH TẾ",
            "giao-duc": "GIÁO DỤC",
            "the-thao": "THỂ THAO",
            "giai-tri": "GIẢI TRÍ",
            "doi-song": "ĐỜI SỐNG",
            "phap-luat": "PHÁP LUẬT",
            "xa-hoi": "XÃ HỘI",
            "van-hoa": "VĂN HÓA",
            "cong-nghe": "CÔNG NGHỆ",
            "khoa-hoc": "KHOA HỌC",
            "xe-co": "XE CỘ",
            "nha-dat": "NHÀ ĐẤT",
            "tien-ich": "TIỆN ÍCH",
        }

        try:
            with transaction.atomic():
                self.stdout.write("🗑️  Đang xóa tất cả Category cũ...")
                Category.objects.all().delete()

                for slug, name in CATEGORY_DATA.items():
                    Category.objects.create(name=name)
                    self.stdout.write(
                        self.style.SUCCESS(f"✔ Đã tạo Category: {name}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f"❌ Lỗi khi seed categories: {str(e)}"))
