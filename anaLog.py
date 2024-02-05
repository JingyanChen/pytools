import re
import pandas as pd

def parse_log_file(log_file_path):
    data = {
        'draw/dispatch_line': [],
        'reason': [],
        'calling_function': [],
        'send_immediately': []
    }

    pattern = re.compile(r'draw/dispatch_line = (\d+), reason = ([^,]+), calling_function = ([^,]+), send immediately = (\d+)')

    with open(log_file_path, 'r') as file:
        for line in file:
            match = pattern.match(line)
            if match:
                data['draw/dispatch_line'].append(int(match.group(1)))
                data['reason'].append(match.group(2).strip())
                data['calling_function'].append(match.group(3).strip())
                data['send_immediately'].append(int(match.group(4)))

    return pd.DataFrame(data)

def save_to_excel(data_frame, excel_file_path):
    data_frame.to_excel(excel_file_path, index=False)

if __name__ == "__main__":
    log_file_path = "addtional_barrier_reasons.log"
    excel_file_path = "outputfile.xlsx"

    log_data = parse_log_file(log_file_path)
    save_to_excel(log_data, excel_file_path)