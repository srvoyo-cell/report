import logging
import os

from dotenv import load_dotenv
from reportai_class import ReportAI


if __name__ == '__main__':
    # ==========================================================
    # НАСТРОЙКА ЛОГИРОВАНИЯ
    # ==========================================================
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )

    load_dotenv()

    report = ReportAI(
        model='Qwen/Qwen3-VL-235B-A22B-Instruct',
        token=os.getenv('HF_TOKEN'),
        base_dir='for_reports',
        output_dir='for_reports/output',
    )
    
    report.make_docx()

