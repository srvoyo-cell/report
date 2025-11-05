plot_functions = [
    {
        "type": "function",
        "function": {
            "name": "generate_plot_functions",
            "description": (
                "Анализирует код и текст отчёта, чтобы сгенерировать Python-функции, "
                "которые строят и сохраняют графики в PNG. "
                "Использует matplotlib.pyplot и plt.savefig()."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "functions": {
                        "type": "array",
                        "description": "Список функций, каждая сохраняет график в PNG.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Имя функции, например 'plot_sin'."
                                },
                                "ready_to_use_code": {
                                    "type": "string",
                                    "description": "Полный исполняемый Python-код, который строит и сохраняет график."
                                }
                            },
                            "required": ["name", "ready_to_use_code"]
                        }
                    }
                },
                "required": ["functions"]
            }
        }
    }
]
