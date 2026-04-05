**ВЕРСИЯ 3.2.1**

Связь осуществляется через HTTP-сообщения. Полезная нагрузка передаётся в виде JSON-документа в теле сообщения.

Запросы на выполнение команд отправляются как POST HTTP/1.1 на /api/`command`.
Запросы на конкретные ресурсы (предпросмотр изображения, пространственный индекс и т.д.) отправляются как GET HTTP/2 на /resource/`type` со строкой запроса id=`id`.

Существует два уровня проверки ошибок.
Во-первых, проверяется общая корректность запроса на уровне HTTP. Сюда входит правильный набор заголовков, валидный JSON-документ в теле и др. Если обнаружена ошибка, немедленно отправляется ответ с пустым телом и заголовком "Reason", содержащим описание ошибки. В противном случае протокол переходит к следующему уровню.
Во-вторых, сам JSON-документ (если применимо) проверяется в соответствии с основной частью данного протокола, и генерируется соответствующий ответ. Наряду с JSON-ошибками, HTTP-статусы используются как общая подсказка о результате запроса.

# Проверка URL

Если запрос был отправлен на неизвестный эндпоинт, отправляется HTTP 400 Bad Request с одним из следующих заголовков "Reason":

Reason: Unknown/unsupported command "`неизвестная команда`" requested.
Reason: The requested resource type "`тип ресурса`" is not supported.

Для запросов **на выполнение команды** строка запроса отсутствует. В противном случае отправляется HTTP 400 Bad Request с пустым телом и заголовком "Reason":

Reason: No query strings allowed for command execution requests.

Для запросов **ресурсов** один параметр "id" является обязательным и ссылается на идентификатор ресурса на сервере; это целое число, большее или равное нулю. В зависимости от типа ресурса могут быть предусмотрены дополнительные параметры, что определено далее в протоколе.

В случае ошибок отправляется HTTP 400 Bad Request с пустым телом и одним из следующих заголовков "Reason":

Reason: Query string must be provided for resource requests.
Reason: Query string must include "id" parameter for resource requests.
Reason: "id" parameter of the query string must be of integer type.
Reason: Invalid value `некорректный id` for "id" parameter of the query string: must be >= 0.

Ответы на запросы, содержащие ошибки в URL, включая ошибки строки запроса, которые зависят от типа ресурса (определены далее в протоколе), являются **единственными** ответами, которые могут не указывать обязательные заголовки HTTP, определённые ниже.

# Обязательные заголовки HTTP

Запросы **на выполнение команды** должны включать следующие HTTP-заголовки:
- Content-Type: application/json; charset=utf-8
- Content-Length: `длина тела запроса в байтах`
- Accept: application/json; charset=utf-8
- Protocol-Version: `версия данного протокола`
- Request-ID: `идентификатор запроса`
Ответы на выполнение команды должны включать следующие HTTP-заголовки:
- Server: `HTTP сервер`
- Content-Type: application/json; charset=utf-8 **ИЛИ** что угодно для ответов не 200
- Content-Length: `длина тела ответа в байтах`
- Protocol-Version: `версия данного протокола`
- Request-ID: `идентификатор запроса`

Запросы **ресурсов** должны включать следующие HTTP-заголовки:
- Accept: `поддерживаемые форматы`
- Protocol-Version: `версия данного протокола`
- Request-ID: `идентификатор запроса`
Ответы на запросы ресурсов должны включать следующие HTTP-заголовки:
- Server: `HTTP сервер`
- Content-Type: `формат ресурса` **ИЛИ** что угодно для ответов не 200
- Content-Length: `длина тела ответа в байтах`
- Protocol-Version: `версия данного протокола`
- Request-ID: `идентификатор запроса`

Для разных запросов ресурсов могут быть определены дополнительные обязательные заголовки в зависимости от типа ресурса.
Любые дополнительные заголовки, генерируемые HTTP-серверами и клиентами, **не нарушают** данный протокол.
Если в запросе отсутствуют все обязательные заголовки, включая дополнительные, зависящие от типа ресурса, HTTP-сервер формирует ответ HTTP 400 Bad Request с пустым телом, заголовком "Request-ID" (если присутствует) и заголовком "Reason":

Reason: Invalid HTTP Request. Headers "`отсутствующие заголовки`" are missing in the request.

Если отсутствует только заголовок "Content-Length", вместо этого отправляется HTTP 411 Length Required со следующим заголовком "Reason":

Reason: Invalid HTTP request. "Content-Length" header must be provided.

Значения обязательных заголовков считаются допустимыми для запросов **на выполнение команды**, если:
- Content-Type и Accept равны "application/json; charset=utf-8" ИЛИ "application/json;charset=utf-8"
- Content-Length имеет целочисленный тип и находится в диапазоне от 2 до 1024 включительно
- Protocol-Version равен фактической версии этого протокола
- Request-ID имеет целочисленный тип и больше или равен 0

Если значение заголовка "Content-Length" превышает 1024, отправляется ответ HTTP 413 Content Too Large с пустым телом и заголовком "Reason":

Reason: Invalid value "`переданная длина`" for "Content-Length" header: must be in [2, 1024] for /api/`command` request.

В остальных случаях отправляется ответ HTTP 400 Bad Request с пустым телом и одним из следующих заголовков "Reason":

Reason: Invalid value "`некорректное значение`" of "Content-Type" header: must be "application/json; charset=utf-8" or "application/json;charset=utf-8" for /api/`command` request.
Reason: Invalid value "`некорректное значение`" of "Accept" header: must be "application/json; charset=utf-8" or "application/json;charset=utf-8" for /api/`command` request.
Reason: Invalid type for "Content-Length" header: must be of integer type.
Reason: Invalid value "`переданная длина`" for "Content-Length" header: must be in [2, 1024] for /api/`command` request.
Reason: Invalid protocol version "`переданная версия`" in "Protocol-Version" header: used protocol version is "`фактическая версия протокола`".
Reason: Invalid type for "Request-ID" header: must be of integer type.
Reason: Invalid value "`значение`" of "Request-ID" header: must be >= 0.

Значения обязательных заголовков считаются допустимыми для запросов **ресурсов**, если:
- Accept равен "image/png" для запросов предпросмотра и "image/tiff" для запросов индексов
- Protocol-Version равен фактической версии этого протокола
- Request-ID имеет целочисленный тип и больше или равен 0

Если какой-либо заголовок некорректен, отправляется ответ HTTP 400 Bad Request с пустым телом и одним из следующих заголовков "Reason":

Reason: Invalid value "`некорректное значение`" of "Accept" header: must be "image/png" for /resource/preview request.
Reason: Invalid value "`некорректное значение`" of "Accept" header: must be "image/tiff" for /resource/index request.
Reason: Invalid protocol version "`переданная версия`" in "Protocol-Version" header: used protocol version is "`фактическая версия протокола`".
Reason: Invalid type for "Request-ID" header: must be of integer type.
Reason: Invalid value "`значение`" of "Request-ID" header: must be >= 0.

# Проверка тела HTTP-запроса

После успешного прохождения проверки HTTP-заголовков запрос переходит к проверке тела. На этом этапе проверяется только то, имеет ли тело правильный тип и правильный формат.

Для запросов **на выполнение команды** (HTTP POST) проверяется, является ли тело корректным JSON-документом. Если нет, отправляется HTTP 400 Bad Request с пустым телом и заголовком "Reason":

Reason: The request's body is not a valid JSON document.

Если тело является пустым JSON-документом, отправляется HTTP 400 Bad Request с пустым телом и заголовком "Reason":

Reason: The request's body must not be an empty JSON document for command execution requests.

Для запросов **ресурсов** (HTTP GET) проверяется, что тело пустое. Если нет, отправляется HTTP 400 Bad Request с пустым телом и заголовком "Reason":

Reason: The request's body must be empty for resource requests.

Если запрос прошёл проверку тела, он переходит ко второму уровню проверки ошибок, связанному с JSON-частью данного протокола.

# Запросы на выполнение команд
## Поддерживаемые команды

1. PING                 - проверить соединение и получить фрагмент данных "PONG"
2. SHUTDOWN             - выключить сервер
3. import_gtiff         - загрузить файл GeoTiff на сервер и кэшировать его
4. calc_preview         - запросить у сервера вычисление предпросмотра изображения из кэшированных GeoTiff-файлов
5. calc_index           - создать спектральный индекс и кэшировать его
6. set_satellite        - сохранить, какой спутник используется в сессии клиента
7. end_session          - освободить ресурсы, занятые клиентом. Обозначает на завершение сессии клиента
8. import_metafile      - загрузить файл метаданных
9. generate_description - сгенерировать текстовое описание индекса

## Структура сообщения

Все JSON-документы состоят из 5 ключей:

**ЗАПРОС**
- `proto_version`     - [СТРОКА] в формате "x.y.z", указывающая версию используемого протокола
- `server_version`    - [СТРОКА] в формате "x.y.z", указывающая версию запущенного сервера
- `id`                - [ЦЕЛОЕ]  идентификатор запроса, >= 0
- `operation`         - [СТРОКА] тип операции, выполняемой на сервере
- `parameters`        - [ОБЪЕКТ] параметры для использования при `operation`

**ОТВЕТ**
- `proto_version`     - [СТРОКА] в формате "x.y.z", указывающая версию используемого протокола
- `server_version`    - [СТРОКА] в формате "x.y.z", указывающая версию запущенного сервера
- `id`                - [ЦЕЛОЕ]  идентификатор соответствующего запроса, >= 0
- `status`            - [ЦЕЛОЕ]  код результата, указывающее на успех или ошибку
- `result`            - [ОБЪЕКТ] данные, сгенерированные соответствующей `operation`, если применимо

Если фактические данные `parameters` или `result` отсутствуют, для этого ключа отправляется пустой объект.

Коды результатов следуют общим правилам:
- 0 означает, что запрошенная операция успешно выполнена
- 1xxxx означает неверный запрос (проверка типов и структуры запроса)
- 2xxxx означает ошибку на стороне сервера (логическая/другая ошибка)
- 100xx и 200xx относятся к кодам, общим для всех операций
- 1yyxx и 2yyxx относятся к кодам, специфичным для операции `yy`, нумеруемой как в "Поддерживаемых командах", с префиксом 0

Ниже приведены особенности запросов и ответов для каждой поддерживаемой команды.

## Общие коды результатов

1. Неверная структура запроса:
    - `status` - 10000
    - `result` - { "error": "key '`неизвестный ключ`' is unknown" }
    -  HTTP 400 Bad Request
2. Неверная структура запроса:
    - `status` - 10001
    - `result` - { "error": "keys '`отсутствующие ключи`' are not specified" }
    -  HTTP 400 Bad Request
3. Неверная строка версии протокола:
    - `status` - 10002
    - `result` - { "error": "invalid protocol version string: '`некорректная строка`'" }
    -  HTTP 400 Bad Request
4. Неверная строка версии сервера:
    - `status` - 10003
    - `result` - { "error": "invalid server version string: '`некорректная строка`'" }
    -  HTTP 400 Bad Request
5. Неверный идентификатор:
    - `status` - 10004
    - `result` - { "error": "invalid request id: '`некорректный id`'" }
    -  HTTP 400 Bad Request
6. Неизвестная операция:
    - `status` - 10005
    - `result` - { "error": "unknown operation '`операция`' requested" }
    -  HTTP 400 Bad Request
7. Неверные параметры:
    - `status` - 10006
    - `result` - { "error": "invalid '`parameters`' key: must be of JSON object type" }
    -  HTTP 400 Bad Request
8. Неверные параметры (отсутствует ключ в объекте `parameters`):
    - `status` - 10007
    - `result` - { "error": "keys '`отсутствующие ключи`' are not specified in '`parameters`' for '`операция`' operation" }
    -  HTTP 400 Bad Request
9. Неверные параметры (неизвестный ключ в объекте `parameters`):
    - `status` - 10008
    - `result` - { "error": "unknown key '`неизвестный ключ`' in '`parameters`' for '`операция`' operation" }
    -  HTTP 400 Bad Request
10. Неправильная версия протокола:
    - `status` - 10009
    - `result` - { "error": "incorrect protocol version: '`запрошенная версия протокола`'. The current protocol version is `используемая версия протокола`" }
    -  HTTP 400 Bad Request
11. Несовпадающие ключи:
    - `status` - 10010
    - `result` - { "error": "values '`несовпадающие ключи`' do not match in request and response" }
    -  HTTP 400 Bad Request
12. Неправильная версия сервера:
    - `status` - 20000
    - `result` - { "error": "incorrect server version: '`запрошенная версия сервера`'. The server runs version `фактическая версия сервера`" }
    -  HTTP 500 Internal Server Error
13. Неподдерживаемая версия протокола:
    - `status` - 20001
    - `result` - { "error": "unsupported protocol version: '`неподдерживаемая версия протокола`'. The server understands protocol versions `поддерживаемые версии протокола`" }
    -  HTTP 500 Internal Server Error
14. Неподдерживаемая операция:
    - `status` - 20002
    - `result` - { "error": "unsupported operation '`неподдерживаемая операция`' requested. Supported operations are `поддерживаемые операции`" }
    -  HTTP 500 Internal Server Error
16. Спутник не задан:
    - `status` - 20003
    - result - { "error": "request `запрос` was received before 'set_satellite' request" }
    - HTTP 500 Internal Server Error

## ping

*ЗАПРОС*

- `operation`  - "PING"
- `parameters` - {}

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - { "data": "PONG" }
    -  HTTP 200 OK
2. Непустые параметры:
    - `status` - 10100
    - `result` - { "error": "'`parameters`' must be an empty object for 'PING' request" }
    -  HTTP 400 Bad Request

## shutdown

*ЗАПРОС*

- `operation`  - "SHUTDOWN"
- `parameters` - {}

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - {}
    -  HTTP 200 OK
2. Непустые параметры:
    - `status` - 10200
    - `result` - { "error": "'`parameters`' must be an empty object for 'SHUTDOWN' request" }
    -  HTTP 400 Bad Request
????????????????????? поддержка асинхронности ?????????????????
3. Сервер занят:
    - `status` - 20200
    - `result` - { "error": "server is busy, performing request `request id`" }
    -  HTTP 503 Service Unavailable
????????????????????? поддержка асинхронности ?????????????????
4. Не удалось закрыть файл:
    - `status` - 20201
    - `result` - { "error": "failed to close '`имя файла`'" }
    -  HTTP 500 Internal Server Error

## import gtiff

**Должен** отправляться только после успешного ответа на запрос 'set_satellite'.

*ЗАПРОС*

- `operation`  - "import_gtiff"
- `parameters` - {
    "file": "`/путь/к/файлу.tif`",  **!!!никаких локальных путей для удалённых серверов; пока нормально!!!**
    "band": `название канала` [СТРОКА]
}
`band` - какому спектральному каналу соответствует файл

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - {
        "file": "`/путь/к/загруженному/файлу.tif`",  **!!!никаких локальных путей для удалённых серверов; пока нормально!!!**
        "band": `канал`                                     [ЦЕЛОЕ],
        "info": {
            "width": `ширина`                               [ЦЕЛОЕ],
            "height": `высота`                              [ЦЕЛОЕ],
            "projection": `проекция`                        [СТРОКА],
            "unit": `единица имзерения`                     [СТРОКА],
            "origin": [`x`, `y`]                            [МАССИВ DOUBLE],
            "pixel_size": [`размер по x`, `размер по y`]    [МАССИВ DOUBLE]
        }
    }
    -  HTTP 200 OK
    `file`          - 
    `band`          - канал загруженного изображения GeoTiff
    `width`         - ширина изображения в пикселях
    `height`        - высота изображения в пикселях
    `projection`    - строка в формате "`authority`:`code`", идентифицирующая используемую проекцию
    `unit`          - единица измерения, используемая в изображении
    `origin`        - координаты начала координат изображения
    `pixel_size`    - размер пикселя изображения в единицах измерения
2. Неверный тип канала:
    - `status` - 10300
    - `result` - { "error": "invalid '`band`' key: must be of string type" }
    -  HTTP 400 Bad Request
3. Не GeoTiff:
    - `status` - 20300
    - `result` - { "error": "provided file '`файл`' is not a GeoTiff image" }
    -  HTTP 500 Internal Server Error
4. Неизвестная ошибка:
    - `status` - 20301
    - `result` - { "error": "failed to open file '`имя файла`'" }
    -  HTTP 500 Internal Server Error

## calculate preview

**Должен** отправляться только после успешного ответа на запрос 'set_satellite'.

*ЗАПРОС*

- `operation`  - "calc_preview"
- `parameters` - {
    "index": `индекс` или "nat_col"  [СТРОКА],
    "width": `нужная ширина`         [ЦЕЛОЕ],
    "height": `нужная высота`        [ЦЕЛОЕ]
}
`index`     - какой индекс вычислить для предпросмотра. "nat_col" обозначает визуализацию в естественных цветах
`width`     - ширина предпросмотра, предпочитаемая клиентом, > 0
`height`    - высота предпросмотра, предпочитаемая клиентом, > 0

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - {
        "url": "/resource/preview?id=`id`   [СТРОКА]
    }
    -  HTTP 200 OK
    `url` - URL для использования в HTTP GET запросе
2. Неверный тип индекса:
    - `status` - 10400
    - `result` - { "error": "invalid '`index`' key: must be of string type" }
    -  HTTP 400 Bad Request
3. Неверный тип ширины или высоты:
    - `status` - 10401
    - `result` - { "error": "invalid '`width or height`' key: must be of integer type" }
    -  HTTP 400 Bad Request
4. Неверная ширина или высота:
    - `status` - 10402
    - `result` - { "error": "invalid `width or height` '`некорректное значение`' in '`width or height`' key: must be > 0" }
    -  HTTP 400 Bad Request
5. Неизвестный/неподдерживаемый индекс:
    - `status` - 20400
    - `result` - { "error": "index '`индекс`' is not supported or unknown" }
    -  HTTP 400 Bad Request
6. Индекс не вычислен:
    - `status` - 20401
    - `result` - { "error": "`индекс или модель-спутника канал` '`название-индекса или номер-канала`' is not `рассчитан или загружен` but needed for preview generation" }
    -  HTTP 500 Internal Server Error
7. Неизвестная ошибка:
    - `status` - 20402
    - `result` - { "error": "unknown error" }
    -  HTTP 500 Internal Server Error

## calculate index

**Должен** отправляться только после успешного ответа на запрос 'set_satellite'.

*ЗАПРОС*

- `operation`  - "calc_index"
- `parameters` - {
    "index": "`название индекса`"  [СТРОКА]
}
`index` - название индекса/алгоритма для вычисления. "water_mask" для бинарного растра классификации воды.

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - {
        "url": "/resource/index?id=`id`"                    [СТРОКА],
        "index": `название индекса`    **!!!пересмотреть для RESTful в будущем!!!**
        "info": {
            "width": `ширина`                               [ЦЕЛОЕ],
            "height": `высота`                              [ЦЕЛОЕ],
            "projection": `проекция`                        [СТРОКА],
            "unit": `единицы измерения`                     [СТРОКА],
            "origin": [`x`, `y`]                            [МАССИВ DOUBLE],
            "pixel_size": [`размер по x`, `размер по y`]    [МАССИВ DOUBLE],
            "min": `мин значение пикселя`                   [ЧИСЛО С ПЛАВАЮЩЕЙ ТОЧКОЙ],
            "max": `макс значение пикселя`                  [ЧИСЛО С ПЛАВАЮЩЕЙ ТОЧКОЙ],
            "mean": `среднее значение пикселя`              [ЧИСЛО С ПЛАВАЮЩЕЙ ТОЧКОЙ],
            "stdev": `стандартное отклонение`               [ЧИСЛО С ПЛАВАЮЩЕЙ ТОЧКОЙ],
            "ph_unit": `физическая величина`                [СТРОКА],
        }
    }
    -  HTTP 200 OK
    `url`           - URL для использования в HTTP GET запросе
    `index`         - 
    `width`         - ширина изображения в пикселях
    `height`        - высота изображения в пикселях
    `projection`    - строка в формате "`authority`:`code`", идентифицирующая используемую проекцию
    `unit`          - единица измерения, используемая в изображении
    `origin`        - координаты начала координат изображения
    `pixel_size`    - размер пикселя изображения в единицах измерения
    `min`           - минимальное значение пикселя
    `max`           - максимальное значение пикселя
    `mean`          - среднее значение пикселя
    `stdev`         - стандартное отклонение значений пикселей
    `ph_unit`       - какую физическую единицу представляют значения пикселей, если есть
2. Неверный тип индекса:
    - `status` - 10500
    - `result` - { "error": "invalid '`index`' key: must be of string type" }
    -  HTTP 400 Bad Request
3. Неизвестный/неподдерживаемый индекс:
    - `status` - 20500
    - `result` - { "error": "index '`индекс`' is not supported or unknown" }
    -  HTTP 400 Bad Request
4. Не поддерживается спутником:
    - `status` - 20501
    - `result` - { "error": "index '`индекс`' is not supported for `модель спутника` `уровень обработки`" }
    -  HTTP 500 Internal Server Error
5. Недостаточно диапазонов:
    - `status` - 20502
    - `result` - { "error": "unable to calculate index '`индекс`': `модель спутника` bands number `нужные каналы` are needed" }
    -  HTTP 500 Internal Server Error
6. Невозможно создать маску воды:
    - `status` - 20503
    - `result` - { "error": "unable to create water mask: water extraction index is not calculated" }
    -  HTTP 500 Internal Server Error
7. Неизвестная ошибка:
    - `status` - 20504
    - `result` - { "error": "unknown error" }
    -  HTTP 500 Internal Server Error

## set satellite

*ЗАПРОС*

- `operation`  - "set_satellite"
- `parameters` - {
    "satellite": "`модель спутника`",    [СТРОКА] какой спутник используется в сессии клиента
    "proc_level": `уровень обработки`    [СТРОКА] какой уровень обработки используется в сессии клиента
    }
`satellite`     - какой спутник используется в сессии клиента
`proc_level`    - какой уровень обработки используется в сессии клиента

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - {}
    -  HTTP 200 OK
2. Неверный тип спутника:
    - `status` - 10600
    - `result` - { "error": "invalid '`satellite`' key: must be of string type" }
    -  HTTP 400 Bad Request
3. Неверный тип proc_level:
    - `status` - 10601
    - `result` - { "error": "invalid '`proc_level`' key: must be of string type" }
    -  HTTP 400 Bad Request
4. Неподдерживаемый спутник:
    - `status` - 20600
    - `result` - { "error": "unsupported satellite model: '`спутник`'" }
    -  HTTP 500 Internal Server Error
5. Неверный proc_level:
    - `status` - 20601
    - `result` - { "error": "unknown/unsupported processing level '`уровень обработки`' for '`спутник`'" }
    -  HTTP 400 Bad Request

## end session

*ЗАПРОС*

- `operation`  - "end_session"
- `parameters` - {}

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - {}
    -  HTTP 200 OK
2. Непустые параметры:
    - `status` - 10700
    - `result` - { "error": "'`parameters`' must be an empty object for 'end_session' request" }
    -  HTTP 400 Bad Request
3. Сервер занят
    - `status` - 20700
    - `result` - { "error": "unable to end session: a request is being processed" }
    -  HTTP 409 Conflict

## import metadata

**Должен** отправляться только после успешного ответа на запрос 'set_satellite'.

*ЗАПРОС*

- `operation`  - "import_metafile"
- `parameters` - {
    "file": "`/путь/к/файлу`"  **!!!никаких локальных путей для удалённых серверов; пока нормально!!!**
}
`file`  - 

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - {
        "loaded": `число`  [ЦЕЛОЕ]
    }
    -  HTTP 200 OK
    `loaded` - количество наборов данных, для которых были прочитаны метаданные
2. Неверный/неправильный файл:
    - `status` - 20800
    - `result` - { "error": "metadata file '`имя файла`' is invalid, unsupported or does not contain calibration coefficients" }
    -  HTTP 500 Internal Server Error
3. Неизвестная ошибка:
    - `status` - 20801
    - `result` - { "error": "failed to open metadata file '`имя файла`'" }
    -  HTTP 500 Internal Server Error

## generate description

*ЗАПРОС*

- `operation`  - "generate_description"
- `parameters` - {
    "index": "`индекс`"     - [СТРОКА],
    "lang": "`код языка`"   - [СТРОКА]
}
`index` - название индекса, для которого генерируется описание. "summary" для общего описания по всем вычисленным индексам.
`lang`  - язык, на котором генерировать описание

*ОТВЕТ*

1. Успех:
    - `status` - 0
    - `result` - {
        "index": `индекс`                  - [СТРОКА],
        "desc": "`текстовое описание`"     - [СТРОКА]
    }
    -  HTTP 200 OK
    `index` - название индекса
    `desc`  - фактическая смысловая интерпретация индекса
2. Неверный тип индекса:
    - `status` - 10900
    - `result` - { "error": "invalid '`index`' key: must be of string type" }
    -  HTTP 400 Bad Request
3. Неверный тип языка:
    - `status` - 10901
    - `result` - { "error": "invalid '`lang`' key: must be of string type" }
    -  HTTP 400 Bad Request
4. Неизвестный/неподдерживаемый индекс:
    - `status` - 20900
    - `result` - { "error": "index '`индекс`' is not supported or unknown" }
    -  HTTP 400 Bad Request
5. Неподдерживаемый язык:
    - `status` - 20901
    - `result` - { "error": "language '`язык`' is not supported" }
    -  HTTP 400 Bad Request
6. Индекс не вычислен:
    - `status` - 20902
    - `result` - { "error": "index '`индекс`' is not calculated" }
    -  HTTP 500 Internal Server Error

## Перекрёстная проверка HTTP и JSON

Если применимо к типу запроса (например, для запросов на выполнение команды), после того как запрос успешно проходит уровень проверки ошибок HTTP и "клиентскую" часть уровня проверки ошибок JSON (коды результатов 1xxxx), которая гарантирует, что JSON-часть содержит действительный запрос в соответствии с данным протоколом, некоторые части HTTP-запроса сравниваются с определёнными ключами JSON-части. Выполняются следующие сравнения:

- Эндпоинт HTTP и ключ JSON `operation`
- Заголовок HTTP "Protocol-Version" и ключ JSON `proto_version`
- Заголовок HTTP "Request-ID" и ключ JSON `id`

Если значения в какой-либо паре не совпадают или относятся к разным сущностям (например, запрос был отправлен в /api/ping, а ключ `operation` содержит 'export_gtiff'), отправляется HTTP 400 Bad Request с тем же содержимым, что и в запросе, и одним из заголовков "Reason":

Reason: Requested operation "`операция`" does not match to the endpoint "/api/`command`".
Reason: Protocol versions do not match in HTTP header and JSON payload: "`версия в заголовке`" and "`версия в теле`".
Reason: Request ids do not match in HTTP header and JSON payload: "`id в заголовке`" and "`id в теле`".

# Запросы ресурсов

Поддерживаются следующие эндпоинты ресурсов:
- /resource/preview     - для 8-битных PNG-предпросмотров изображений GeoTiff
- /resource/index       - для изображений GeoTiff

Все запросы ресурсов формируются как HTTP/2 GET запросы с пустым телом, заголовками, определёнными в разделе "Обязательные заголовки HTTP", и, возможно, дополнительными заголовками в зависимости от типа ресурса, а также строкой запроса с обязательным параметром `id`, равным целому числу > 0, и, возможно, дополнительными параметрами в зависимости от типа ресурса.

## Preview

Получив ответ "status: 0" на запрос `calc_preview`, клиент может сформировать запрос ресурса для получения фактического изображения предпросмотра:

GET /resource/preview?id=`id`&sb=`0|1`&mask=`0|1` HTTP/2
Accept: image/png
Protocol-Version: `версия данного протокола`
Request-ID: `id`

Значение параметра "id" берётся из ответа сервера на соответствующий запрос "calc_preview".
Параметр "sb" означает "scalebar" (масштабная линейка) и определяет, должна ли быть сгенерирована масштабная линейка для предпросмотра. Может быть '0' (без линейки) или '1' (генерировать линейку).
Параметр "mask" определяет, должно ли быть включено наложение водной маски для предпросмотра. Может быть '0' (без маски) или '1' (включить маску).

Ответ:

HTTP/2 200 OK
Server: `HTTP сервер`
Content-Type: image/png
Content-Length: `длина тела ответа в байтах`
Protocol-Version: `версия данного протокола`
Request-ID: `идентификатор запроса`
Width: `ширина`
Height: `высота`

`двоичное представление`

Перед обработкой запроса ресурса сервер проверяет полученную строку запроса на наличие параметров, специфичных для предпросмотра, и в случае ошибок отправляет HTTP 400 Bad Request с пустым телом и одним из следующих заголовков "Reason":

Reason: Query string must include "sb" parameter for preview requests.
Reason: Query string must include "mask" parameter for preview requests.
Reason: Unknown parameter in query string for preview request.
Reason: "sb" parameter of the query string must be either 0 or 1.
Reason: "mask" parameter of the query string must be either 0 or 1.

Если предпросмотр с запрошенным id не является полутоновым (чёрно-белым), а параметр "sb" равен '1', отправляется HTTP 400 Bad Request с пустым телом и заголовком "Reason":

Reason: Unable to generate a scalebar for a non-grayscale preview.

Если параметр "mask" равен '1', а водная маска не может быть сгенерирована, отправляется HTTP 500 Internal Server Error с пустым телом и заголовком "Reason":

Reason: Unable to generate a water mask. Probably, water index was not created for the scene.

Если предпросмотр с запрошенным URL отсутствует, отправляется HTTP 404 Not Found с пустым телом и заголовком "Reason":

Reason: Requested preview "`url запроса`" does not exist.

## Index

Запросы на получение индексов предназначены для получения фактического геоизображения и сохранения его на машине клиента. Дополнительные обязательные заголовки или параметры строки запроса не определены.

GET /resource/index?id=`id` HTTP/2
Accept: image/tiff
Protocol-Version: `версия данного протокола`
Request-ID: `id`

Ответ:

HTTP/2 200 OK
Server: `HTTP сервер`
Content-Type: image/tiff
Content-Length: `длина тела ответа в байтах`
Protocol-Version: `версия данного протокола`
Request-ID: `идентификатор запроса`

`двоичное представление`

Перед обработкой запроса ресурса сервер проверяет, содержит ли полученная строка запроса только параметр "id". В противном случае сервер отправляет HTTP 400 Bad Request с пустым телом и заголовком "Reason":

Reason: Query string must only include "id" parameter for index requests.

Если индекс с запрошенным URL отсутствует, отправляется HTTP 404 Not Found с пустым телом и заголовком "Reason":

Reason: Requested index "`url запроса`" does not exist.

# Примеры

**Проверить связь с сервером**

*ЗАПРОС*

POST /api/PING HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 13
Content-Length: 125
Connection: Keep-Alive
User-Agent: Mozilla/5.0

{
    "id": 13,
    "operation": "PING",
    "parameters": {},
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 125
Protocol-Version: 3.2.1
Request-ID: 13
Server: nginx

{
  "id": 13,
  "proto_version": "3.2.1",
  "result": {
    "data": "PONG"
  },
  "server_version": "1.0.0",
  "status": 0
}

**Выключить сервер**

*ЗАПРОС*

POST /api/SHUTDOWN HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 13
Content-Length: 129

{
    "id": 13,
    "operation": "SHUTDOWN",
    "parameters": {},
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 103
Protocol-Version: 3.2.1
Request-ID: 13
Server: nginx

{
  "id": 13,
  "proto_version": "3.2.1",
  "result": {},
  "server_version": "1.0.0",
  "status": 0
}

**Задать модель спутника**

*ЗАПРОС*

POST /api/set_satellite HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 13
Content-Length: 204

{
    "id": 13,
    "operation": "set_satellite",
    "parameters": {
        "proc_level": "L1TP",
        "satellite": "Landsat 8/9"
    },
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 103
Protocol-Version: 3.2.1
Request-ID: 13
Server: nginx

{
  "id": 13,
  "proto_version": "3.2.1",
  "result": {},
  "server_version": "1.0.0",
  "status": 0
}

**Загрузить снимок Landsat**

*ЗАПРОС*

POST /api/import_gtiff HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 21
Content-Length: 287

{
    "id": 21,
    "operation": "import_gtiff",
    "parameters": {
        "band": "6",
        "file": "/home/user/Test data/LC08_L1TP_108031_20240821_20240830_02_T1/LC08_L1TP_108031_20240821_20240830_02_T1_B6.TIF"
    },
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 489
Protocol-Version: 3.2.1
Request-ID: 21
Server: nginx

{
  "id": 21,
  "proto_version": "3.2.1",
  "result": {
    "band": "6",
    "file": "/home/user/Test data/LC08_L1TP_108031_20240821_20240830_02_T1/LC08_L1TP_108031_20240821_20240830_02_T1_B6.TIF",
    "info": {
      "height": 7921,
      "origin": [
        328485.0,
        4741515.0
      ],
      "pixel_size": [
        30.0,
        -30.0
      ],
      "projection": "EPSG:32654",
      "unit": "metre",
      "width": 7801
    }
  },
  "server_version": "1.0.0",
  "status": 0
}

**Загрузить файл метаданных**

*ЗАПРОС*

POST /api/import_metafile HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 26
Content-Length: 270

{
    "id": 26,
    "operation": "import_metafile",
    "parameters": {
        "file": "/home/user/Test data/LC08_L1TP_108031_20240821_20240830_02_T1/LC08_L1TP_108031_20240821_20240830_02_T1_MTL.txt"
    },
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 125
Protocol-Version: 3.2.1
Request-ID: 26
Server: nginx

{
  "id": 26,
  "proto_version": "3.2.1",
  "result": {
    "loaded": 11.0
  },
  "server_version": "1.0.0",
  "status": 0
}

**Рассчитать цветное превью**

*ЗАПРОС*

POST /api/calc_preview HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 28
Content-Length: 210

{
    "id": 28,
    "operation": "calc_preview",
    "parameters": {
        "height": 265,
        "index": "nat_col",
        "width": 319
    },
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 142
Protocol-Version: 3.2.1
Request-ID: 28
Server: nginx

{
  "id": 28,
  "proto_version": "3.2.1",
  "result": {
    "url": "/resource/preview?id=1"
  },
  "server_version": "1.0.0",
  "status": 0
}

**Рассчитать чёрно-белое превью для индекса NSMI**

*ЗАПРОС*

POST /api/calc_preview HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 41
Content-Length: 207

{
    "id": 41,
    "operation": "calc_preview",
    "parameters": {
        "height": 206,
        "index": "nsmi",
        "width": 459
    },
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 142
Protocol-Version: 3.2.1
Request-ID: 41
Server: nginx

{
  "id": 41,
  "proto_version": "3.2.1",
  "result": {
    "url": "/resource/preview?id=2"
  },
  "server_version": "1.0.0",
  "status": 0
}

**Рассчитать индекс NSMI**

*ЗАПРОС*

POST /api/calc_index HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 31
Content-Length: 160

{
    "id": 31,
    "operation": "calc_index",
    "parameters": {
        "index": "nsmi"
    },
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 567
Protocol-Version: 3.2.1
Request-ID: 31
Server: nginx

{
  "id": 31,
  "proto_version": "3.2.1",
  "result": {
    "index": "nsmi",
    "info": {
      "height": 7921,
      "max": 0.7617611289024353,
      "mean": 0.007320965174585581,
      "min": -0.42250141501426697,
      "origin": [
        328485.0,
        4741515.0
      ],
      "ph_unit": "--",
      "pixel_size": [
        30.0,
        -30.0
      ],
      "projection": "EPSG:32654",
      "stdev": 0.09729105234146118,
      "unit": "metre",
      "width": 7801
    },
    "url": "/resource/index?id=21"
  },
  "server_version": "1.0.0",
  "status": 0
}

**Сгенерировать описание для индекса NSMI на русском языке**

*ЗАПРОС*

POST /api/generate_description HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 35
Content-Length: 192

{
    "id": 35,
    "operation": "generate_description",
    "parameters": {
        "index": "nsmi",
        "lang": "ru"
    },
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 493
Protocol-Version: 3.2.1
Request-ID: 35
Server: nginx

{
  "id": 35,
  "proto_version": "3.2.1",
  "result": {
    "desc": "\u0420\u0430\u0441\u0441\u0447\u0438\u0442\u0430\u043d\u043e \u043f\u043e \u043e\u0442\u0440\u0430\u0436\u0430\u0442\u0435\u043b\u044c\u043d\u043e\u0439 \u0441\u043f\u043e\u0441\u043e\u0431\u043d\u043e\u0441\u0442\u0438 \u0432\u0435\u0440\u0445\u043d\u0435\u0433\u043e \u0441\u043b\u043e\u044f \u0430\u0442\u043c\u043e\u0441\u0444\u0435\u0440\u044b.\n",
    "index": "nsmi"
  },
  "server_version": "1.0.0",
  "status": 0
}

**Завершить сессию клиента**

*ЗАПРОС*

POST /api/end_session HTTP/1.1
Content-Type: application/json; charset=utf-8
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-Id: 72
Content-Length: 137

{
    "id": 72,
    "operation": "end_session",
    "parameters": {
    },
    "proto_version": "3.2.1",
    "server_version": "1.0.0"
}

*ОТВЕТ*

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 103
Protocol-Version: 3.2.1
Request-ID: 72
Server: nginx

{
  "id": 72,
  "proto_version": "3.2.1",
  "result": {},
  "server_version": "1.0.0",
  "status": 0
}

**Получить превью**

*ЗАПРОС*

GET /resource/preview?id=4&sb=1&mask=0 HTTP/2
Protocol-Version: 3.2.1
Request-Id: 71
Accept: image/png



*ОТВЕТ*

HTTP/2 200 OK
Protocol-Version: 3.2.1
Request-ID: 71
Content-Type: image/png
Width: 203
Height: 206
Server: nginx

`binary representation`

**Получить индекс**

*ЗАПРОС*

GET /resource/index?id=25 HTTP/2
Protocol-Version: 3.2.1
Request-Id: 56
Accept: image/tiff



*ОТВЕТ*

HTTP/2 200 OK
Protocol-Version: 3.2.1
Request-ID: 56
Content-Type: image/tiff
Content-Length: 61839619
Server: nginx

`binary representation`

**Некорректный запрос**

*ЗАПРОС*

POST /api/export_gtiff HTTP/1.1
Content-Type: application/json; charset=utf-8
Content-Length: 218
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-ID: 152

{
    "proto_version": "3.2.1",
    "server_version": "1.0.0",
    "id": 152,
    "operation": "export_geotiff",
    "parameters": {
        "id": "4",
        "file": "/home/user/gis/landsat/indices/ndci.tif"
    }
}

*ОТВЕТ*

HTTP/2 400 Bad Request
Server: nginx
Content-Type: application/json; charset=utf-8
Content-Length: 187
Protocol-Version: 3.2.1
Request-ID: 152

{
    "proto_version": "3.2.1",
    "server_version": "1.0.0",
    "id": 152,
    "status": 10005,
    "result": {
        "error": "unknown operation 'export_geotiff' requested"
    }
}

**Некорректный запрос**

*ЗАПРОС*

POST /api/PING HTTP/1.1
Accept: application/json; charset=utf-8
Protocol-Version: 3.2.1
Request-ID: 152

{
    "proto_version": "3.2.1",
    "server_version": "1.0.0",
    "id": 152,
    "operation": "PING",
    "parameters": {}
}

*ОТВЕТ*

HTTP/2 400 Bad Request
Server: nginx
Content-Type: application/json; charset=utf-8
Content-Length: 0
Protocol-Version: 3.2.1
Request-ID: 152
Reason: Invalid HTTP Request. Headers "Content-Type, Content-Length" are missing in the request.

**Некорректный запрос**

*ЗАПРОС*

GET /resource/index HTTP/1.1
Protocol-Version: 3.2.1
Request-Id: 56
Accept: image/tiff



*ОТВЕТ*

HTTP/1.1 400 Bad Request
Protocol-Version: 3.2.1
Request-ID: 56
Content-Type: image/tiff
Content-Length: 61839619
Server: nginx
Reason: Query string must be provided for resource requests.

