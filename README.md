# med-demo

Для успешного запуска:

1. Файлы flask_service.py и transform_json.py поместите в директорию spert (нейросетевая модель)
2. Для запуска сервиса на flask в командной строке введите:

    `python ./flask_service.py predict --config configs/spert-predict_RDRS-ext_XLM-R-sag.conf`
    
3. Для запуска React приложения в другом окне командной строки:

    `cd react-webapp-med`
    
    `npm start`
