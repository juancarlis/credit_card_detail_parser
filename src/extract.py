import logging
import re
from typing import List, Tuple
from pathlib import Path

import pandas as pd
from PyPDF2 import PdfFileReader


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    file_name = 'eresumen_visa_202306'
    raw_file_path = f'Data/raw/{file_name}.pdf'

    # Extracting raw data from PDF
    text: List[str] = extract_text_from_pdf(file_path=raw_file_path)

    text = find_valuable_data_interval(text=text)

    # Remove duplicates within each line
    text = [_remove_duplicates_from_line(line) for line in text]

    # Extracting data into DataFrame
    output = extract_data(text=text)

    # Making sure processed path exists
    processed_path: Path = Path('Data/outputs')
    ensure_directory_exists(directory=processed_path)
    
    # Creating export routes
    csv_file_path = processed_path / f'processed_{file_name}.csv'
    xl_file_path = processed_path / f'processed_{file_name}.xlsx'

    # Exporting data
    save_to_csv(df=output, file_path=csv_file_path)
    save_to_excel(df=output, file_path=xl_file_path)


def extract_text_from_pdf(file_path: str) -> List[str]:
    """Extracts text from the first page of a PDF file."""
    logger.info('Extracting text from raw PDF')
    with open(file_path, 'rb') as f:
        reader = PdfFileReader(f)
        page = reader.getPage(0)
        return page.extract_text().split('\n')


def find_valuable_data_interval(text: List[str]) -> List[str]:
    """Finds and returns valuable data within the text."""
    logger.info('Excluding not useful data.')
    start_line, end_line = 0, 0
    for line_nb, line in enumerate(text):
        if re.search('BONIFICACION ACUERDOS GLOBALES', line) != None:
            start_line = line_nb

        if re.search('PAGO MINIMO', line) != None:
            end_line = line_nb

    return text[start_line:end_line]


def extract_data(text: List[str]) -> pd.DataFrame: 
    """ 
    Extracts dates, descriptions and values from the given text 
    and returns them as dataframe.

    Parameters:
    - text: List[str], The text lines to process

    Returns:
    - pd.Dataframe, A DataFrame with the extracted data
    """
    
    logger.info('Extracting data')

    # Regular expressions for dates and values
    date_regex = re.compile(r'\d{2}\.\d{2}\.\d{2}')
    value_regex = re.compile(r'\d{1,3}(?:\.\d{3})*(?:,\d{2})?')

    # Lists to store the extracted data
    dates: List[str] = []
    descriptions: List[str] = []
    values: List[str] = []

    # Iterate through each line to extract data
    for line in text:
        # Search for date
        date_match = re.search(date_regex, line)
        if date_match:
            # Search for values
            value_matches = re.findall(value_regex, line)
            if value_matches:
                # Extract date
                date = date_match.group()
                
                # Si el último valor es "0,00", usa el penúltimo valor
                # Conditionally extract value and description
                value = value_matches[-2] if value_matches[-1] == '0,00' else value_matches[-1]
                description = line[date_match.end():line.rfind(value)].strip()

                dates.append(date)
                descriptions.append(description)
                values.append(value)

    # Create a DataFrame
    data = pd.DataFrame({
        'Fecha': dates,
        'Descripcion': descriptions, 
        'Valores': values 
        })

    # Clean and transform data
    data['Fecha'] = data['Fecha'].str.replace('.', '/', regex=True).apply(pd.to_datetime, format='%d/%m/%y')
    data['Valores'] = data['Valores'].str.replace('.', '', regex=True).str.replace(',', '.').astype(float)

    # Negate the values that do not correspond to 'BONIFICACION ACUERDOS GLOBALES'
    devolucion_de_cargos_mask = data['Descripcion'].str.contains(
                'BONIFICACION ACUERDOS GLOBALES', 
                case=False, 
                na=False
                )

    data.loc[~devolucion_de_cargos_mask, 'Valores'] = \
            data.loc[~devolucion_de_cargos_mask, 'Valores'].apply(lambda r: r*-1)

    return data 


def ensure_directory_exists(directory: Path) -> None:
    """Creates directory if it not exists."""
    if not directory.exists():
        directory.mkdir(parents=True)
        logger.info(f'Directory created: {directory}.')


def save_to_csv(df: pd.DataFrame, file_path: Path) -> None:
    """Exports df (dataframe) to CSV file."""
    try: 
        df.to_csv(
                file_path, 
                encoding='utf-8-sig', 
                sep=';', 
                decimal=',', 
                index=False
                )
        logger.info(f'Data succesfully exported to CSV on {file_path}')
    except Exception as e:
        logger.error(f'Error on exporting data to CSV: {e}')


def save_to_excel(df: pd.DataFrame, file_path: Path) -> None:
    """Exports df (dataframe) to Excel file."""
    try: 
        df.to_excel(
                file_path, 
                index=False
                )
        logger.info(f'Data succesfully exported to Excel on {file_path}')
    except Exception as e:
        logger.error(f'Error on exporting data to Excel: {e}')


def _remove_duplicates_from_line(line: str) -> str:
    # Divide la linea en dos partes
    half_index = len(line) // 2
    first_half = line[:half_index].strip()
    second_half = line[half_index:].strip()
    
    # Compares two parts and if are both equal keeps only one
    if first_half == second_half:
        return first_half
    else:
        return line


if __name__ == '__main__':
    main()
