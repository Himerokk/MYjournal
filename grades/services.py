import requests
from bs4 import BeautifulSoup

def get_schedule():
    sheet_id = "1QxI_sdewEffwRj1H2Nju4QN-KDjTDzqxPYyyl3fkWSo"
    # Используем /view, так как он доступен без авторизации
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/view"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr') # Получаем все строки таблицы
        
        target_col_idx = None
        
        # ШАГ 1: Динамически находим индекс столбца нашей группы
        for row in rows:
            cells = row.find_all('td')
            for idx, cell in enumerate(cells):
                val = cell.get_text().strip()
                if "11 ИСиП-В" == val:
                    target_col_idx = idx
                    break
            if target_col_idx is not None:
                break

        # Если не нашли заголовок группы, выходим
        if target_col_idx is None:
            print("Ошибка: Столбец группы 11 ИСиП-В не найден")
            return []

        schedule_data = []
        start_collecting = False

        # ШАГ 2: Читаем строго по найденному столбцу
        for row in rows:
            cells = row.find_all('td')
            if len(cells) > target_col_idx:
                # Берем текст только из нашей "вертикали"
                text = cells[target_col_idx].get_text().strip()
                
                # Начинаем сбор данных после того, как встретили Хализеву (первая пара)
                if "Хализева" in text:
                    start_collecting = True
                
                if start_collecting and text:
                    # Пропускаем повторное упоминание группы
                    if text == "11 ИСиП-В":
                        continue
                        
                    # Защита от дубликатов из-за объединенных ячеек Google
                    if not schedule_data or schedule_data[-1]['name'] != text:
                        schedule_data.append({'name': text})
            
            # Ограничиваем выборку (например, 8 пар на ближайшее время)
            if len(schedule_data) >= 8:
                break
        
        print(f"Успешно собрано пар: {len(schedule_data)}")
        return schedule_data

    except Exception as e:
        print(f"Критическая ошибка парсинга: {e}")
        return []