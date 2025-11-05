# =====================================================
# ИМПОРТЫ
# =====================================================
import openai
import os
import re
import logging
import docx2txt
import pypandoc
import subprocess
import shutil
import templates as ts
import httpx

from typing import Optional
from jinja2 import Template
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
            cls_dir: str
            
    ):
        
        self.model = model
        self.token = token
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.cls_dir = cls_dir
        self.client: Optional[object] = None
        self.theory_text: str = ""
        self.code_complete: str = ""
        self.theory_fixed: str = ""
        self.report_sections: str = ""

    # ------------------------------------------------------------
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ------------------------------------------------------------

    @log_method
    def __extract_latex_body(self, tex: str) -> str:
        """Извлекает тело LaTeX между \\begin{document} и \\end{document}."""
        m = re.search(r'\\begin\{document\}(.+?)\\end\{document\}', tex, flags=re.DOTALL)
        if m:
            return m.group(1).strip()
        tex = re.sub(r'\\documentclass(\[.*?\])?\{.*?\}', '', tex)
        tex = re.sub(r'\\usepackage(\[.*?\])?\{.*?\}', '', tex)
        return tex.replace('\\begin{document}', '').replace('\\end{document}', '').strip()

    @log_method
    def __clean_llm_output(self, text: str) -> str:
        """Удаляет markdown и служебные элементы."""
        text = re.sub(r'(?m)^#{1,6}.*$', '', text)
        text = re.sub(r'```latex|```', '', text)
        return text.strip()

    @log_method
    def __run_xelatex_and_log(self, texfile: str = "report.tex", runs: int = 2) -> None:
        """Компилирует LaTeX-файл и выводит ошибки."""
        for i in range(runs):
            logging.info(f"Запуск xelatex: попытка {i + 1}/{runs}")
            proc = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", texfile],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if proc.returncode != 0:
                logging.error(proc.stderr)
                raise RuntimeError(f"LaTeX compilation failed: {proc.returncode}")
        logging.info("✅ Компиляция успешна.")

    @log_method
    def __connect_to_client(self) -> None:
        """Подключает клиента LLM."""
        logging.info("Подключение к LLM...")

        self.client = openai.OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=self.token,
            http_client=httpx.Client(timeout=httpx.Timeout(360.0))
        )

    @log_method
    @staticmethod
    def __create_figures(response):
        tool_calls = response["choices"][0]["message"].get("tool_calls", [])
        if tool_calls:
            for call in tool_calls:
                if call["function"]["name"] == "generate_plot_functions":
                    data = call["function"]["arguments"]
                    for f in data["functions"]:
                        exec(f["ready_to_use_code"])


    @log_method
    def __dataload(self) -> None:
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
    def __stream_chat_completion(self, prompt: str) -> str:
        """Выполняет потоковый вызов LLM с постепенным чтением вывода."""
        logging.info("Начинается потоковая генерация...")

        # Собираем параметры динамически
        kwargs = dict(
            model=self.model,
            input=[{"role": "user", "content": prompt}],
            stream=True,
            temperature=0,
        )

        stream = self.client.responses.create(**kwargs)

        final_text = ""
        print()

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
    def __make_report(self) -> None:
        """Формирует разделы отчёта, обращаясь к LLM."""
        self.__connect_to_client()
        self.__dataload()

        logging.info("Этап 1 — восстановление теоретической части...")
        prompt_theory = ts.build_theory_prompt(self.theory_text)

        raw_theory = self.__stream_chat_completion(prompt_theory)

        self.theory_fixed = self.__extract_latex_body(self.__clean_llm_output(raw_theory))

        logging.info("Этап 2 — генерация раздела 'Ход работы'...")
        progress_prompt = ts.build_progress_prompt(self.theory_fixed, self.code_complete)

        raw_report = self.__stream_chat_completion(progress_prompt)

        self.report_sections = self.__extract_latex_body(self.__clean_llm_output(raw_report))
        logging.info("✅ Разделы отчёта успешно сгенерированы.")

    # ------------------------------------------------------------
    # СОХРАНЕНИЕ И КОМПИЛЯЦИЯ
    # ------------------------------------------------------------

    @log_method
    def make_tex(self) -> str:
        """Создаёт и сохраняет LaTeX-файл отчёта."""
        self.__make_report()

        tex_template = ts.make_latex_template(self.report_sections)

        os.makedirs(self.output_dir, exist_ok=True)
        tex_path = os.path.join(self.output_dir, "report.tex")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_template)

        logging.info(f"✅ LaTeX-файл сохранён: {tex_path}")
        return tex_path

    @log_method
    def make_pdf(self) -> str:
        """Компилирует LaTeX-файл в PDF."""
        tex_path = self.make_tex()
        os.chdir(self.output_dir)
        self.__create_figures(self.response)
        self.__run_xelatex_and_log(os.path.basename(tex_path))
        pdf_path = tex_path.replace(".tex", ".pdf")
        logging.info(f"✅ PDF готов: {pdf_path}")
        return pdf_path
