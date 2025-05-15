import re
import openpyxl
import os

def extract_numbers_and_rounds_from_html(html):
    # Expressões regulares para capturar os números e as rodadas
    number_matches = re.finditer(r'data-role="number-\d+".*?<span class="value--dd5c7">(\d+)</span>', html)
    extracted_data = []

    for match in number_matches:
        extracted_data.append(int(match.group(1)))

    return extracted_data

def process_html_to_excel(input_file, output_excel_file):
    # Abrir o arquivo HTML de entrada
    with open(input_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Extrair números e rodadas do HTML
    extracted_numbers = extract_numbers_and_rounds_from_html(html_content)

    # Criar uma nova planilha Excel
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Números Extraídos"

    # Adicionar os números à planilha
    for i, num in enumerate(extracted_numbers, start=1):
        sheet.cell(row=i, column=1, value=num)

    # Salvar o arquivo Excel
    workbook.save(output_excel_file)
    print(f"Números extraídos e salvos em Excel: {output_excel_file}")

# Obter o caminho da área de trabalho
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Definir caminhos dos arquivos
input_html_file = os.path.join(desktop_path, "jogadas roleta.txt")  # Caminho do arquivo HTML de entrada
output_excel_file = os.path.join(desktop_path, "historico roleta immersive2.xlsx")       # Caminho do arquivo Excel de saída

# Processar o HTML diretamente para Excel
process_html_to_excel(input_html_file, output_excel_file)
