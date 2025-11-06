# =====================================================
# ИМПОРТЫ
# =====================================================
import openai
import os
import logging
import docx2txt
import pypandoc
import subprocess
import templates as ts
import httpx
import json

from typing import Optional
from help_functions import log_method


# ==========================================================
# ОСНОВНОЙ КЛАСС
# ==========================================================
class ReportAI:
    def __init__(
            self,
            model: str,
            token: str,
            base_dir: str,
            output_dir: str,
    ):
        self.model = model
        self.token = token
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.client: Optional[object] = None
        self.theory_text: str = ""
        self.code_complete: str = ""
        self.theory_fixed: str = ""
        self.report_sections: str = ""

    # ------------------------------------------------------------
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ------------------------------------------------------------

    @log_method
    def _connect_to_client(self) -> None:
        """Подключает клиента LLM."""
        logging.info("Подключение к LLM...")

        self.client = openai.OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=self.token,
            http_client=httpx.Client(timeout=httpx.Timeout(600.0))
        )

    @log_method
    def _dataload(self) -> None:
        """Загружает теоретическую часть и исходный код."""
        logging.info("Загрузка данных из директории...")
        theory_path = os.path.join(self.base_dir, "theory.docx")
        self.theory_text = ' '.join(docx2txt.process(theory_path).split())

        code_parts = []
        for filename in sorted(os.listdir(self.base_dir)):
            if filename.endswith((".py", ".cpp", ".r", ".R")):
                with open(os.path.join(self.base_dir, filename), "r", encoding="utf-8") as f:
                    code_parts.append(f"\n# ===== {filename} =====\n{f.read()}\n")

        self.code_complete = '\n'.join(code_parts)

    # ------------------------------------------------------------
    # ОСНОВНОЙ ПРОЦЕСС
    # ------------------------------------------------------------

    @log_method
    def _stream_chat_completion(self, prompt: str) -> str:
        """Выполняет потоковый вызов LLM с постепенным чтением вывода."""
        logging.info("Начинается потоковая генерация...")

        kwargs = dict(
            model=self.model,
            input=[{"role": "user", "content": prompt}],
            stream=True,
            temperature=0,
        )

        stream = self.client.responses.create(**kwargs)
        final_text = ""

        for event in stream:
            if event.type == "response.completed":
                output = event.response.output[0]
                if output.content and len(output.content) > 0:
                    final_text = output.content[0].text
                break

        if not final_text:
            logging.warning("⚠️ Модель не вернула текст. Проверь лог или соединение.")
            final_text = "[ОШИБКА: пустой ответ от модели]"

        print("Ответ:", final_text)
        logging.info("✅ Потоковая генерация завершена.")
        return final_text

    @log_method
    def _make_report(self) -> None:
        """Формирует разделы отчёта, обращаясь к LLM."""
        self._connect_to_client()
        self._dataload()

        logging.info("Этап 1 — восстановление теоретической части...")
        prompt_theory = ts.build_theory_prompt(self.theory_text)
        self.theory_fixed = self._stream_chat_completion(prompt_theory)

        logging.info("Этап 2 — генерация раздела 'Ход работы'...")
        progress_prompt = ts.build_progress_prompt(self.theory_fixed, self.code_complete)
        self.report_sections = self._stream_chat_completion(progress_prompt)

        logging.info("✅ Разделы отчёта успешно сгенерированы.")

    @log_method
    def _make_code_response(self, text: str) -> str:
        """Сохраняет код для построения графиков в txt-файл."""
        os.makedirs(self.output_dir, exist_ok=True)
        txt_resp = text.split('♣')[-1]
        self.resp_path = os.path.join(self.output_dir, 'resp.txt')

        with open(self.resp_path, 'w', encoding='utf-8') as f:
            f.write(txt_resp)

        logging.info(f"✅ Txt-файл сохранён: {self.resp_path}")
        return self.resp_path

    @log_method
    def _create_graphics(self):
        """Создаёт графики, если есть код."""
        script_path = getattr(self, "resp_path", os.path.join(self.output_dir, "resp.txt"))

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Код для графиков не найден: {script_path}")

        with open(script_path, 'r', encoding='utf-8') as file:
            code = json.load(file)['ready_to_use_code']

        try:
            os.chdir('/for_reports/output')
            proc = subprocess.run(
                ["python", '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300
            )
            if proc.returncode != 0:
                logging.error(f"Ошибка при выполнении графиков: {proc.stderr}")
                raise RuntimeError(f"Ошибка при выполнении графиков: {proc.returncode}")
            logging.info("✅ Графики успешно созданы.")
        except subprocess.TimeoutExpired:
            logging.error("Время выполнения скрипта для графиков превысило лимит.")
            raise
    # ------------------------------------------------------------
    # СОХРАНЕНИЕ И КОНВЕРТАЦИЯ
    # ------------------------------------------------------------

    @log_method
    def make_md(self) -> str:
        """Создаёт и сохраняет Markdown-файл отчёта."""
        self._make_report()

        os.makedirs(self.output_dir, exist_ok=True)
        self.md_path = os.path.join(self.output_dir, "report.md")

        with open(self.md_path, "w", encoding="utf-8") as f:
            f.write(self.report_sections)

        logging.info(f"✅ Markdown-файл сохранён: {self.md_path}")
        return self.md_path


    @log_method
    def make_docx(self, reference_doc: Optional[str] = None, highlight_style: str = 'haddock') -> str:
        """Создаёт DOCX-файл отчёта, используя pypandoc."""
        os.makedirs(self.output_dir, exist_ok=True)

        if not hasattr(self, "md_path") or not self.md_path:
            self.md_path = os.path.join(self.output_dir, "report.md")

        if os.path.exists(self.md_path):
            logging.info(f"🟡 Обнаружен существующий Markdown-файл: {self.md_path}. Пропускаем генерацию.")
        else:
            logging.info("Markdown-файл не найден. Генерация нового отчёта...")
            self.make_md()

        # Создание графиков, если код есть
        logging.info("Создание графиков для отчёта...")
        try:
            if self.report_sections :
                self._make_code_response(self.report_sections)
                self._create_graphics()
            elif os.path.exists('for_reports/output/resp.txt'):
                self._create_graphics()
            else:
                logging.info("Код для графиков не найден в report_sections — пропускаем создание графиков.")
        except Exception as e:
            logging.error(f"Ошибка при создании графиков: {e}")

        # Конвертация markdown → docx
        docx_path = self.md_path.replace(".md", ".docx")
        extra_args = [
            f"--highlight-style={highlight_style}",
            "--standalone"
        ]
        if reference_doc:
            extra_args.append(f'--reference-doc={reference_doc}')

        try:
            pypandoc.convert_text(
                open(self.md_path, 'r', encoding='utf-8').read(),
                'docx',
                format='md',
                outputfile=docx_path,
                extra_args=extra_args
            )
            logging.info(f"✅ DOCX успешно создан: {docx_path}")
        except Exception as e:
            logging.error(f"Ошибка при конвертации Markdown → DOCX: {e}")
            raise

        return docx_path
