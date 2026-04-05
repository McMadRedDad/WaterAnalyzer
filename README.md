Bachelor's thesis project in GIS. RTU MIREA, Moscow

Monorepo for client-server app that helps analyze water body ecological state by spectral indices using Landsat 8/9 imagery.
Provides an automated workflow for quick preliminary water body analysis and prepares data for futher manual analysis in general purpose GIS applications.

NDWI, ANDWI, WI<sub>2015</sub>, NSMI, OC<sub>3</sub>, NDBI indices and temperature evaluation are implemented.
Landsat 8 and 9 Collection 2 Tier 1 Level 1 and 2 datasets are supported. For Level 1 datasets, indices and temperature rasters may be calculated either for Top Of Atmosphere (TOA) or for Land Surface (LS). For LS temperature from Level 1 datasets basic 1 parameter Dark Object Subtraction (DOS1) atmospheric correction is performed. The temperature itself is evaluated taking land surface emissivity from MODIS Emissivity Library into account.

Caution icon used for frontend comes from Freepik: <a href="https://www.flaticon.com/free-icons/caution" title="caution icons">Caution icons created by Freepik - Flaticon</a>

---------------

Бакалаврский дипломный проект по ГИС. РТУ МИРЭА, Москва

Монорепо клиент-серверного приложения для анализа экологического состояния водных объектов с помощью спектральных индексов по спутниковым снимкам Landsat 8/9.
Предоставляет автоматизированный воркфлоу для быстрого предварительного анализа водных объектов и подготавливает данные для дальнейшего ручного анализа в ГИС-приложениях общего назначения.

Реализованы индексы NDWI, ANDWI, WI<sub>2015</sub>, NSMI, OC<sub>3</sub>, NDBI, а также расчёт температуры.
Поддерживаются снимки Landsat 8 и 9 Collection 2 Tier 1 Level 1 и 2. Для снимков Level 1 имеется возможность рассчитывать индексы и растры температуры для верхнего слоя атмосферы (TOA) или для поверхности Земли (LS). Для расчёта LS температуры по данным Level 1 применяется простая поправка на влияние атмосферы методом вычитания тёмного тела с одним параметром (DOS1). Сами значения температуры вычисляются с учётом коэффициента излучения поверхности из MODIS Emissivity Library.

Иконка предупреждающего знака, использованная для фронтенда, с сайта Freepik: <a href="https://www.flaticon.com/free-icons/caution" title="caution icons">Caution icons created by Freepik - Flaticon</a>