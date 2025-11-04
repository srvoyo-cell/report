# =====================================================
# ИМПОРТЫ
# =====================================================
import ollama
import huggingface_hub
import os
import re
import logging
import docx2txt
import pypandoc
import subprocess
import shutil


from typing import Optional
from jinja2 import Template
from templates import *
from help_functions import * 


# ==========================================================
# ОСНОВНОЙ КЛАСС
# ==========================================================
class ReportAI:
    def __init__(self, model: str, token: str, platform: str,
                 base_dir: str, output_dir: str, cls_dir: str):
        self.model = model
        self.token = token
        self.platform = platform
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
        if self.platform == 'ollama':
            self.client = ollama.Client(
                host="https://ollama.com",
                headers={'Authorization': self.token}
            )
        else:
            self.client = huggingface_hub.InferenceClient(
                model=self.model,
                token=self.token,
                timeout=600.0,  # клиент всё равно нужен для открытия потока
            )

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
        full_output = ""

        # Потоковая итерация по токенам
        for event in self.client.chat_completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=4096,
            temperature=0.7
        ):
            if event is None:
                continue

            # Hugging Face отдаёт события в виде объектов с типом
            if hasattr(event, "delta") and event.delta and hasattr(event.delta, "content"):
                token = event.delta.content
                if token:
                    print(token, end="", flush=True)
                    full_output += token

        print()  # чтобы не залипало в консоли
        logging.info("✅ Потоковая генерация завершена.")
        return full_output

    @log_method
    def __make_report(self) -> None:
        """Формирует разделы отчёта, обращаясь к LLM."""
        self.__connect_to_client()
        self.__dataload()

        logging.info("Этап 1 — восстановление теоретической части...")
        prompt_theory = build_theory_prompt(self.theory_text)

        if isinstance(self.client, ollama.Client):
            res = self.client.chat(model=self.model, messages=[{'role': 'user', 'content': prompt_theory}])
            raw_theory = res['message']['content']
        else:
            raw_theory = self.__stream_chat_completion(prompt_theory)

        self.theory_fixed = self.__extract_latex_body(self.__clean_llm_output(raw_theory))

        logging.info("Этап 2 — генерация раздела 'Ход работы'...")
        progress_prompt = build_progress_prompt(self.theory_fixed, self.code_complete)

        if isinstance(self.client, ollama.Client):
            response = self.client.chat(model=self.model, messages=[{"role": "user", "content": progress_prompt}])
            raw_report = response['message']['content']
        else:
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

        LATEX_TEMPLATE = r"""
\documentclass{university-report}
\usepackage{pdfpages}
\usepackage{fontspec}
\setmainfont{Times New Roman}

\begin{document}

\structsection{Теоретическая часть}
{{ theory_fixed }}

\structsection{Ход работы}
{{ report_sections }}

\end{document}
"""
        os.makedirs(self.output_dir, exist_ok=True)
        tex_path = os.path.join(self.output_dir, "report.tex")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(Template(LATEX_TEMPLATE).render(
                theory_fixed=self.theory_fixed,
                report_sections=self.report_sections
            ))

        logging.info(f"✅ LaTeX-файл сохранён: {tex_path}")
        return tex_path

    @log_method
    def make_pdf(self) -> str:
        """Компилирует LaTeX-файл в PDF."""
        tex_path = self.make_tex()
        os.chdir(self.output_dir)
        self.__run_xelatex_and_log(os.path.basename(tex_path))
        pdf_path = tex_path.replace(".tex", ".pdf")
        logging.info(f"✅ PDF готов: {pdf_path}")
        return pdf_path
