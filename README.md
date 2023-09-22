# med-demo
Репозиторий включает:
- flask сервис-обёртка для сперта (файлы flask_service.py и transform_json.py)
- react приложение - фронт для отображения результатов разбора.

## flask back service for spert
1. Скачать обученные модели сперта (/s/ls4/groups/g0126/pretrain_models/SpERT/spert_XLM-R-sag_RDRS-ext), нормализации (/s/ls4/users/romanrybka/pharm_er/Pipeline_Ner_Norm/RelationExtraction/models/Norm_models) и rubert-cased-base (на хаггинфейс). Скачать файл с PT меддры pt_rus.asc. 
2. Перед запуском настроить пути в следующих файлах: flask_service.py (в начале файла в path добавить путь к папке с модулем normalize, конструкция os.path.dirname(__file__) + '/normalization' не всегда работает); service_config.py; spert-predict_RDRS-ext_XLM-R-sag.conf. А также в файлах модели для нормализации нужно поменять пути в файле CV_config.json.
3. Указать порт в service_config.
4. Установить зависимости из requirements.txt
5. Запустить flask_service.py. Если в скрипте задать флаг IS_DEBUG_WITHOUT_SERVICE=True, то функции протестируются без запуска сервиса.
    `python ./flask_service.py`

Для запуска в production flask.run не рекомендуется. Сейчас используется пакет waitress
```commandline
pip install waitress
waitress-serve --host 127.0.0.1 --port 8081 --threads 1 flask_service:app
```
## react front app
Отладка проводилась с node-v16.17.1-linux-x64.

Чтобы отладить react приложение локально, придётся сделать следующее (пока не знаю, как этот процесс настроить без этих костылей):

- в файле package.json добавить строку `"proxy": "http://194.87.237.6:8081/"` или `"proxy": "http://localhost:8081/"` (в зависимости от того, где запущен flask) (как в коммите [73346119edd853f7ea5331c9717d2db220bd35ed](https://github.com/sag111/med-demo-service_react/blob/73346119edd853f7ea5331c9717d2db220bd35ed/react-webapp-med/package.json))
- в src/App.js убрать слэш в строке `return fetch('./process/'` -> `return fetch('/process'`
- возможно убрать `"homepage": ".",` в package.json, но вроде не должно мешать.

После этого, находясь папке react-webapp-med, ввести:
```commandline
npm install
npm start
```

Можно ещё попробовать тестировать production версию. Для этого:
- установить serve `sudo npm install -g serve`
- создать билд `npm run build`
- запустить билд: `serve -s build`
- Но будут скорее всего проблемы со связью с flask_service. Сейчас всё настроено так, чтоб работало через апач. Через serve на локалхосте надо как-то по другому делать.

Для встраивания на сайт sagteam.ru (выше указанные костыли с proxy и fetch не нужны):
- создать билд `npm run build`
- переместить содержимое папки build в /var/www/html/med-demo
- убедиться, что в настройках apache2 (default-ssl.conf) указаны ProxyPass и ProxyPassReverse связывающие url на который будет посылаться запрос (fetch в  App.js) и ip:port сервера на котором развернут flask_service.

# TODO
1. Сделать, чтоб на фронте при нажатии кнопка становилась недоступной для нажатия и показывалось ожидание.
2. Добавить шапку как на сайте для возврата домой.
3. Проверить многопоточность и обработку нескольких запросов. Было бы круто добавить очередь, но наверно это уже лишнее.
4. Сделать, чтоб на фласк сервисе по / выводился статус моделей, работают/нет, а по другому адресу уже обработка шла. Только не забыть ещё и в апаче это прописать.