# med-demo
Репозиторий включает:
- flask сервис-обёртка для сперта (файлы flask_service.py и transform_json.py)
- react приложение - фронт для отображения результатов разбора.

## flask back service for spert
0. Для запуска нужна папка spert из репозитория [sag111/RelationExtraction](https://github.com/sag111/RelationExtraction/tree/master/spert). Для тестов использовалась папка с коммита [5dc2066212f43278401b6ecb708a20b04580f8f1](https://github.com/sag111/RelationExtraction/tree/5dc2066212f43278401b6ecb708a20b04580f8f1). И файлы модели. Подробное описание кода инференса в [Asans](https://app.asana.com/0/1201137782398817/1203064745486533/f).
1. Файлы flask_service.py и transform_json.py поместите в директорию spert.
2. Задать в flask_service.py порт для прослушки.
3. Пример запуска flask сервиса:

    `python ./flask_service.py predict --config configs/spert-predict_RDRS-ext_XLM-R-sag.conf`

## react front app
Отладка проводилась с node-v16.17.1-linux-x64.

Для отладки реакт приложения надо ввести `npm start` находясь папке react-webapp-med. Но перед этим придётся сделать следующее (пока не знаю, как этот процесс настроить без этих костылей):
- в файле package.json добавить строку "proxy": "http://194.87.237.6:8081/" (как в коммите [73346119edd853f7ea5331c9717d2db220bd35ed](https://github.com/sag111/med-demo-service_react/blob/73346119edd853f7ea5331c9717d2db220bd35ed/react-webapp-med/package.json))
- в src/App.js заменить строку `return fetch('./process/'` на `return fetch('/'`
- в flask_service.py заменить `app.run(host='127.0.0.1', port=3000, threaded = True, debug=True)` на  `app.run(host='194.87.237.6', port=3000, threaded = True, debug=True)`
- возможно убрать `"homepage": ".",` в package.json

Можно ещё попробовать тестировать production версию. Для этого:
- установить serve `sudo npm install -g serve`
- создать билд `npm run build`
- запустить билд: `serve -s build`
- Но будут скорее всего проблемы со связью с flask_service. Сейчас всё настроено так, чтоб работало через апач. Через serve на локалхосте надо как-то по другому делать.

Для встраивания на сайт sagteam.ru:
- создать билд `npm run build`
- переместить содержимое папки build в /var/www/html/med-demo
- убедиться, что в настройках apache2 (default-ssl.conf) указаны ProxyPass и ProxyPassReverse связывающие url на который будет посылаться запрос (fetch в  App.js) и ip:port сервера на котором развернут flask_service.

# TODO
1. Изменить: сейчас в фласк сервисе сперта пришедший текст сохраняется в файл, и трейнер сперта считывает этот файл. Потом сохраняет выходы в другой файл. У всех файлов фиксированные имена с хардкодом. Это не правильно, not thread-safe итп. Надо, чтоб данные между функциями передавались, а не через диск.
2. Сделать, чтоб на фронте при нажатии кнопка становилась недоступной для нажатия и показывалось ожидание.
3. Добавить шапку как на сайте для возврата домой.
4. Проверить многопоточность и обработку нескольких запросов. Было бы круто добавить очередь, но наверно это уже лишнее.
5. Сделать, чтоб на фласк сервисе по / выводился статус моделей, работают/нет, а по другому адресу уже обработка шла. Только не забыть ещё и в апаче это прописать.