#include "mainwindow.hpp"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), ui(new Ui::MainWindow) {
    ui->setupUi(this);

    self.import_p = new ImportPage();
    self.process_p = new ProcessPage();
    self.result_p = new ResultPage();
    change_page(PAGE::IMPORT);
    self.proc_level = PROC_LEVEL::PROC_LEVEL_BAD;

    backend_ip = QHostAddress::LocalHost;
    backend_port = 42069;
    net_man = new QNetworkAccessManager(this);
    proto = JsonProtocol("1.0.0");

    connect(&timer_status, &QTimer::timeout, [this]() { ui->lbl_status->clear(); });
    retries = 3;
    curr_try = 0;
}

MainWindow::~MainWindow() {
    delete ui;
    delete self.import_p;
    delete self.process_p;
    delete self.result_p;
    delete net_man;
}

void MainWindow::send_request(QString type, QJsonObject data, QMap<QString, QString> options) {
    if (backend_ip.isNull()) {
        return;
    }

    if (type == "command") {
        QNetworkRequest req("http://" + backend_ip.toString() + ":" + QString::number(backend_port) + "/api/"
                            + data["operation"].toString());
        req.setHeader(QNetworkRequest::ContentTypeHeader, "application/json; charset=utf-8");
        req.setRawHeader("Accept", "application/json; charset=utf-8");
        req.setRawHeader("Protocol-Version", proto.get_proto_version().toUtf8());
        req.setRawHeader("Request-ID", QString::number(data["id"].toInt()).toUtf8());
        self.req_ids.append(data["id"].toInt());
        lock_interface();
        QNetworkReply *response = net_man->post(req, QJsonDocument(data).toJson());
        connect(response, &QNetworkReply::errorOccurred, this, [this, response] {
            handle_error(response);
            response->deleteLater();
        });
        connect(response, &QNetworkReply::finished, [this, response, options] {
            if (response->error() == QNetworkReply::NoError) {
                process_post(response->request().url(), response->headers(), response->readAll(), options);
            }
            response->deleteLater();
        });
    } else if (type == "resource") {
        QJsonObject     result = data["result"].toObject();
        QNetworkRequest req("http://" + backend_ip.toString() + ":" + QString::number(backend_port) + result["url"].toString());
        req.setRawHeader("Protocol-Version", proto.get_proto_version().toUtf8());
        req.setRawHeader("Request-ID", QString::number(proto.get_counter()).toUtf8());

        QString type = result["url"].toString();
        type = type.split('?').first().split('/').last();
        if (type == "preview") {
            if (!options.contains("scalebar")) {
                return;
            }
            if (!options.contains("mask")) {
                return;
            }
            req.setUrl(req.url().toString() + "&sb=" + options.value("scalebar") + "&mask=" + options.value("mask"));
            req.setRawHeader("Accept", "image/png");
        } else if (type == "index") {
            req.setRawHeader("Accept", "image/tiff");
        } else {
            return;
        }
        proto.inc_counter();

        self.req_ids.append(proto.get_counter() - 1);
        lock_interface();
        QNetworkReply *response = net_man->get(req);
        connect(response, &QNetworkReply::errorOccurred, [this, response]() {
            handle_error(response);
            response->deleteLater();
        });
        connect(response, &QNetworkReply::finished, [this, response, options]() {
            if (response->error() == QNetworkReply::NoError) {
                process_get(response->request().url(), response->headers(), response->readAll(), options);
            }
            response->deleteLater();
        });
    }
}

void MainWindow::handle_error(QNetworkReply *response) {
    if (!response->attribute(QNetworkRequest::HttpStatusCodeAttribute).isValid()) {
        append_log("bad", "Ошибка соединения с сервером: " + response->errorString() + ".");
        set_status_message(false, "Ошибка соединения с сервером");
        change_page(PAGE::IMPORT);
        self.req_ids.clear();
        lock_interface();
        return;
    }

    size_t l = self.req_ids.length();
    uint   id = response->request().rawHeader("request-id").toUInt();
    for (size_t i = 0; i < l; i++) {
        if (self.req_ids[i] == id) {
            self.req_ids.remove(i);
            lock_interface();
            break;
        }
    }

    if (response->hasRawHeader("reason")) {
        append_log("bad",
                   QString("Некорректный HTTP-запрос к серверу: %1 %2, Reason: %3")
                       .arg(response->attribute(QNetworkRequest::HttpStatusCodeAttribute).toString(),
                            response->attribute(QNetworkRequest::HttpReasonPhraseAttribute).toString(),
                            QString::fromUtf8(response->rawHeader("reason"))));
        set_status_message(false, "Некорректный HTTP-запрос");
        return;
    }

    QJsonDocument jdoc = QJsonDocument::fromJson(response->readAll());
    if (jdoc.isNull()) {
        append_log("bad",
                   QString("Неизвестная ошибка на сервере. Ответ сервера: %1 %2.")
                       .arg(response->attribute(QNetworkRequest::HttpStatusCodeAttribute).toString(),
                            response->attribute(QNetworkRequest::HttpReasonPhraseAttribute).toString()));
        set_status_message(false, "Неизвестная ошибка на сервере");
        return;
    }

    QJsonObject json = jdoc.object();
    append_log("bad",
               "Некорректный JSON-запрос к серверу: " + QString::number(json["status"].toInt()) + " "
                   + json["result"].toObject()["error"].toString() + ".");
    set_status_message(false, "Некорректный JSON-запрос");
}

void MainWindow::process_get(QUrl endpoint, QHttpHeaders headers, QByteArray body, QMap<QString, QString> options) {
    size_t l = self.req_ids.length();
    uint   id = headers.value("request-id").toUInt();
    for (size_t i = 0; i < l; i++) {
        if (self.req_ids[i] == id) {
            self.req_ids.remove(i);
            lock_interface();
            break;
        }
    }

    QString type = endpoint.toString();
    type = type.split('?').first().split('/').last();
    if (type == "preview") {
        if (!options.contains("preview_type")) {
            return;
        }
        QPixmap preview;
        preview.loadFromData(body, "PNG");
        if (options.value("preview_type") == "color") {
            self.process_p->set_preview(preview);
        } else {
            self.result_p->set_preview(options.value("preview_type"), preview);
        }
    } else if (type == "index") {
        QString path = QFileDialog::getSaveFileName(this, "Сохранить файл GeoTiff", self.dir.path());
        if (path.isEmpty()) {
            append_log("bad", "Запись файла отменена.");
            set_status_message(false, "Файл не сохранён");
            return;
        }
        if (!(path.endsWith(".tif") || path.endsWith(".tiff") || path.endsWith(".TIF") || path.endsWith(".TIFF"))) {
            path.append(".tif");
        }
        QFile file(path);
        if (!file.open(QIODevice::WriteOnly)) {
            append_log("bad", "Не удалось открыть файл " + path + " для записи.");
            set_status_message(false, "Не удалось открыть файл для записи");
            return;
        }
        qint64 written = file.write(body);
        if (written != body.size()) {
            append_log("bad", "Не удалось записать файл " + path + " целиком. Скорее всего, файл повреждён.");
            set_status_message(false, "Не удалось записать файл");
        } else {
            append_log("good", "Файл " + path + " сохранён.");
            set_status_message(true, "Файл сохранён");
        }
    } else {
        append_log("info", "Запрошена неизвестный тип ресурса, но сервер его обработал: " + type + ".");
        set_status_message(false, "Неизвестный тип ресурса");
    }
}

void MainWindow::process_post(QUrl endpoint, QHttpHeaders headers, QByteArray body, QMap<QString, QString> options) {
    size_t l = self.req_ids.length();
    uint   id = headers.value("request-id").toUInt();
    for (size_t i = 0; i < l; i++) {
        if (self.req_ids[i] == id) {
            self.req_ids.remove(i);
            lock_interface();
            break;
        }
    }

    QString     command = endpoint.toString().split("/").last();
    QJsonObject result = QJsonDocument::fromJson(body).object()["result"].toObject();
    if (command == "PING") {
        append_log("good", "Связь с сервером установлена.");
        set_status_message(true, "Связь с сервером установлена");
    } else if (command == "SHUTDOWN") {
        append_log("good", "Сервер завершил работу.");
        set_status_message(true, "Сервер завершил работу");
    } else if (command == "import_gtiff") {
        for (DATASET &ds : self.datasets) {
            if (ds.filename == result["file"].toString() && ds.band == result["band"].toString()) {
                QJsonObject info = result["info"].toObject();
                ds.width = info["width"].toInt();
                ds.height = info["height"].toInt();
                ds.projection = info["projection"].toString();
                ds.unit = info["unit"].toString();
                ds.origin[0] = info["origin"].toArray()[0].toDouble();
                ds.origin[1] = info["origin"].toArray()[1].toDouble();
                ds.pixel_size[0] = info["pixel_size"].toArray()[0].toDouble();
                ds.pixel_size[1] = info["pixel_size"].toArray()[1].toDouble();
                break;
            }
        }
        append_log("info", "Файл " + result["file"].toString() + " загружен.");
        set_status_message(true, "Файл загружен");
    } else if (command == "calc_preview") {
        send_request("resource", QJsonDocument::fromJson(body).object(), options);
    } else if (command == "calc_index") {
        DATASET ds;
        ds.index = result["index"].toString();
        ds.url = result["url"].toString();
        QJsonObject info = result["info"].toObject();
        ds.width = info["width"].toInt();
        ds.height = info["height"].toInt();
        ds.projection = info["projection"].toString();
        ds.unit = info["unit"].toString();
        ds.origin[0] = info["origin"].toArray()[0].toDouble();
        ds.origin[1] = info["origin"].toArray()[1].toDouble();
        ds.pixel_size[0] = info["pixel_size"].toArray()[0].toDouble();
        ds.pixel_size[1] = info["pixel_size"].toArray()[1].toDouble();
        ds.min = info["min"].toDouble();
        ds.max = info["max"].toDouble();
        ds.mean = info["mean"].toDouble();
        ds.stdev = info["stdev"].toDouble();
        ds.ph_unit = info["ph_unit"].toString();
        self.datasets.append(ds);

        if (get_type_by_index(ds.index) == "water") {
            send_request("command", proto.calc_index("water_mask"));
        }
        if (ds.index != "water_mask") {
            uint width = self.result_p->get_preview_width();
            uint height = self.result_p->get_preview_height();
            send_request("command", proto.calc_preview(ds.index, width, height), options);
            send_request("command", proto.generate_description(ds.index, "ru"));
        }

        self.result_p->set_caption(get_type_by_index(ds.index), ds.index.toUpper());
        self.result_p->set_statistics(get_type_by_index(ds.index), ds.min, ds.max, ds.mean, ds.stdev, ds.ph_unit);

        append_log("info", "Индекс " + result["index"].toString() + " рассчитан.");
        set_status_message(true, "Индекс рассчитан");
    } else if (command == "set_satellite") {
        for (DATASET &ds : self.datasets) {
            send_request("command", proto.import_gtiff(ds.filename, ds.band));
        }
        if (self.proc_level != PROC_LEVEL::LANDSAT_L2SP) {
            send_request("command", proto.import_metafile(self.metadata_file));
        }
        append_log("info", "Модель спутника задана.");
        set_status_message(true, "Спутник задан");
    } else if (command == "end_session") {
        append_log("info", "Сессия сброшена.");
        set_status_message(true, "Сессия сброшена");
    } else if (command == "import_metafile") {
        if (result["loaded"].toInt() != self.datasets.length() - 1) {
            if (curr_try < retries) {
                QTimer::singleShot(500, [this]() {
                    send_request("command", proto.import_metafile(self.metadata_file));
                    curr_try++;
                });
            } else {
                curr_try = 0;
                append_log("bad",
                           QString("Метаданные загружены только для %1 из %2 каналов.")
                               .arg(QString::number(result["loaded"].toInt()), QString::number(self.datasets.length())));
                set_status_message(false, "Метаданные загружены не для всех каналов");
            }
        } else {
            curr_try = 0;
            append_log("info", "Файл метаданных загружен.");
            set_status_message(true, "Метаданные загружены");
            bool cloud = false;
            for (DATASET &ds : self.datasets) {
                if (ds.band == "QA_PIXEL") {
                    cloud = true;
                }
            }
            if (!cloud) {
                append_log("info", "Отсутствует растр оценки качества. Вычисления будут производиться без учёта облаков.");
                set_status_message(false, "Нет растра оценки качества");
            }
        }
    } else if (command == "generate_description") {
        QString index = result["index"].toString(), desc = result["desc"].toString();
        if (index == "summary") {
            self.result_p->set_description("summary", desc);
        } else {
            self.result_p->set_description(get_type_by_index(index), desc);
        }
        append_log("info", QString("Текстовое описание индекса %1 создано.").arg(index));
        set_status_message(true, "Текстовое описание создано");
    } else {
        append_log("info", "Запрошена неизвестная команда, но сервер её обработал: " + command + ".");
        set_status_message(false, "Неизвестная команда");
    }
}

QString MainWindow::get_type_by_index(QString index) {
    QString indx = index.toLower();
    if (indx == "wi2015" || indx == "andwi" || indx == "ndwi") {
        return "water";
    } else if (indx == "water_mask") {
        return "";
    } else if (indx == "nsmi") {
        return "tss";
    } else if (indx == "oc3") {
        return "chloro";
    } else if (indx == "cdom_ndwi") {
        return "cdom";
    } else if (indx == "toa_temperature_landsat" || indx == "ls_temperature_landsat") {
        return "temp";
    } else {
        return "";
    }
}

QString MainWindow::get_index_by_type(QString type) {
    if (type == "summary") {
        return "water_mask";
    } else if (type == "water") {
        for (DATASET &ds : self.datasets) {
            if (ds.index == "wi2015" || ds.index == "andwi" || ds.index == "ndwi") {
                return ds.index;
            }
        }
        return "";
    } else if (type == "tss") {
        for (DATASET &ds : self.datasets) {
            if (ds.index == "nsmi") {
                return ds.index;
            }
        }
        return "";
    } else if (type == "chloro") {
        for (DATASET &ds : self.datasets) {
            if (ds.index == "oc3") {
                return ds.index;
            }
        }
        return "";
    } else if (type == "cdom") {
        for (DATASET &ds : self.datasets) {
            if (ds.index == "cdom_ndwi") {
                return ds.index;
            }
        }
        return "";
    } else if (type == "temp") {
        for (DATASET &ds : self.datasets) {
            if (ds.index == "toa_temperature_landsat" || ds.index == "ls_temperature_landsat") {
                return ds.index;
            }
        }
        return "";
    } else {
        return "";
    }
}

void MainWindow::set_status_message(bool good, QString message, short msec) {
    if (timer_status.isActive()) {
        timer_status.stop();
    }

    if (good) {
        ui->lbl_status->setStyleSheet("color: lightgreen;");
    } else {
        ui->lbl_status->setStyleSheet("color: tomato;");
    }
    ui->lbl_status->setText(message);

    timer_status.start(msec);
}

void MainWindow::append_log(QString type, QString line) {
    QString html;
    QString time = QDateTime::currentDateTime().time().toString();
    if (type == "good") {
        html = "<span style=\"color: lightgreen;\"> [" + time + "]: " + line + "</span>";
    } else if (type == "bad") {
        html = "<span style=\"color: tomato;\"> [" + time + "]: " + line + "</span>";
    } else if (type == "info") {
        html = "[" + time + "]: " + line;
    } else {
        html = "[" + time + "]: " + line;
    }
    ui->plainTextEdit_log->appendHtml(html);
}

bool MainWindow::parse_filenames(QStringList filenames) {
    if (filenames.isEmpty()) {
        return false;
    }
    int counter = 0;
    for (const QString &f : filenames) {
        QString entry = f.toUpper();
        if (entry.endsWith(".TIF") && (entry.right(7).contains('B') || entry.contains("QA_PIXEL"))) {
            if (self.proc_level == PROC_LEVEL::PROC_LEVEL_BAD) {
                if (entry.contains("L1TP")) {
                    self.proc_level = PROC_LEVEL::LANDSAT_L1TP;
                } else if (entry.contains("L2SP")) {
                    self.proc_level = PROC_LEVEL::LANDSAT_L2SP;
                } else {
                    append_log("bad",
                               QString("Уровень обработки снимка %1 не поддерживается. Для спутника Landsat доступны только уровень 1 и 2.")
                                   .arg(f));
                    set_status_message(false, "Неподдерживаемый уровень обработки снимка");
                    return false;
                }
            }

            DATASET ds;
            ds.filename = f;
            QString band = f.right(8);
            if (band[0] == '_') {
                ds.band = band.mid(2, 2);
            } else {
                ds.band = band.mid(3, 1);
            }
            if (entry.contains("QA_PIXEL")) {
                ds.band = "QA_PIXEL";
            }
            self.datasets.append(ds);
            counter++;
        } else if (entry.endsWith("_MTL.TXT")) {
            self.metadata_file = f;
        }
    }
    if (counter == 0) {
        append_log("bad", QString("В выбранной директории %1 нет снимков Landsat или Sentinel.").arg(QDir(filenames[0]).absolutePath()));
        set_status_message(false, "В выбранной директории нет снимков");
        return false;
    }
    return true;
}

void MainWindow::change_page(PAGE to) {
    self.import_p->hide();
    self.process_p->hide();
    self.result_p->hide();
    ui->widget_main->layout()->removeWidget(self.import_p);
    ui->widget_main->layout()->removeWidget(self.process_p);
    ui->widget_main->layout()->removeWidget(self.result_p);

    switch (to) {
    case PAGE::IMPORT: {
        auto directory = [this](QDir dir) {
            QStringList filenames = dir.entryList();
            for (QString &f : filenames) {
                f.prepend(dir.absolutePath() + '/');
            }
            bool ok = parse_filenames(filenames);
            if (!ok) {
                return;
            }
            switch (self.proc_level) {
            case PROC_LEVEL::LANDSAT_L1TP:
                send_request("command", proto.set_satellite("Landsat 8/9", "L1TP"));
                break;
            case PROC_LEVEL::LANDSAT_L2SP:
                send_request("command", proto.set_satellite("Landsat 8/9", "L2SP"));
                break;
            default:
                break;
            }
            self.dir = dir;
            ui->lbl_dir->setText(self.dir.dirName());
            change_page(PAGE::SELECTION);
        };
        auto files = [this](QStringList filenames) {
            bool ok = parse_filenames(filenames);
            if (!ok) {
                return;
            }
            switch (self.proc_level) {
            case PROC_LEVEL::LANDSAT_L1TP:
                send_request("command", proto.set_satellite("Landsat 8/9", "L1TP"));
                break;
            case PROC_LEVEL::LANDSAT_L2SP:
                send_request("command", proto.set_satellite("Landsat 8/9", "L2SP"));
                break;
            default:
                break;
            }
            self.dir = filenames[0].section('/', 0, -2);
            ui->lbl_dir->setText(self.dir.dirName());
            change_page(PAGE::SELECTION);
        };
        auto custom_files = [this](QString proc_level, QString metafile, QList<QPair<QString, QString>> bands_files) {
            if (bands_files.isEmpty()) {
                append_log("bad", "Не выбрано ни одного файла Tiff.");
                set_status_message(false, "Файлы Tiff не выбраны");
                return;
            }
            for (auto &f : bands_files) {
                DATASET ds;
                ds.filename = f.second;
                ds.band = f.first;
                self.datasets.append(ds);
            }
            if (proc_level == "L1TP") {
                self.proc_level = PROC_LEVEL::LANDSAT_L1TP;
            } else if (proc_level == "L2SP") {
                self.proc_level = PROC_LEVEL::LANDSAT_L2SP;
            }
            switch (self.proc_level) {
            case PROC_LEVEL::LANDSAT_L1TP:
                send_request("command", proto.set_satellite("Landsat 8/9", "L1TP"));
                break;
            case PROC_LEVEL::LANDSAT_L2SP:
                send_request("command", proto.set_satellite("Landsat 8/9", "L2SP"));
                break;
            default:
                break;
            }
            self.metadata_file = metafile;
            self.dir = bands_files[0].second.section('/', 0, -2);
            ui->lbl_dir->setText(self.dir.dirName());
            change_page(PAGE::SELECTION);
        };

        disconnect(self.process_p, nullptr, nullptr, nullptr);
        disconnect(self.result_p, nullptr, nullptr, nullptr);
        disconnect(this, &MainWindow::metadata, nullptr, nullptr);
        connect(self.import_p, &ImportPage::custom_bands_page, [this]() {
            self.page = PAGE::IMPORT_CUSTOM_BANDS;
            ui->pb_back->show();
        });
        connect(self.import_p, &ImportPage::satellite_select_page, [this]() {
            self.page = PAGE::IMPORT;
            ui->pb_back->hide();
        });
        connect(self.import_p, &ImportPage::bad_band, [this](QString file) {
            append_log("bad", QString("Выбранный файл %1 не является файлом Tiff.").arg(file));
            set_status_message(false, "Выбранный файл не Tiff");
        });
        connect(self.import_p, &ImportPage::bad_metafile, [this](QString file) {
            append_log("bad", QString("Выбранный файл %1 не является текстовым файлом.").arg(file));
            set_status_message(false, "Выбранный файл не текстовый");
        });
        connect(this, &MainWindow::to_satellite_select_page, self.import_p, &ImportPage::to_satellite_select_page);
        connect(self.import_p, &ImportPage::directory, directory);
        connect(self.import_p, &ImportPage::files, files);
        connect(self.import_p, &ImportPage::custom_files, custom_files);

        self.page = PAGE::IMPORT;
        self.dir = QDir();
        self.proc_level = PROC_LEVEL::PROC_LEVEL_BAD;
        self.metadata_file = "";
        ui->lbl_dir->setText("");
        self.datasets.clear();

        self.process_p->clear_preview();
        if (self.import_p->get_page() == ImportPage::MAIN) {
            ui->pb_back->hide();
        } else if (self.import_p->get_page() == ImportPage::CUSTOM_BANDS) {
            self.page = PAGE::IMPORT_CUSTOM_BANDS;
        }
        ui->widget_main->layout()->addWidget(self.import_p);
        self.import_p->show();
        break;
    }
    case PAGE::SELECTION: {
        auto preview = [this](uint width, uint height) {
            QMap<QString, QString> options = {{"preview_type", "color"}, {"scalebar", "0"}, {"mask", "0"}};
            send_request("command", proto.calc_preview("nat_col", width, height), options);
        };
        auto metadata = [this]() {
            QStringList vals;
            DATASET     ds = self.datasets[0];
            QStringList keys_l;
            QString     keys;
            for (DATASET &ds : self.datasets) {
                keys_l.append(ds.band);
            }
            keys_l.sort();
            for (QString &k : keys_l) {
                keys.append(k.prepend('B') + ", ");
            }
            keys.chop(2);
            vals.append("Landsat 8/9");
            vals.append(QString::number(self.datasets.length()));
            vals.append(keys);
            vals.append(QString::number(ds.width));
            vals.append(QString::number(ds.height));
            vals.append(ds.projection);
            vals.append(ds.unit);
            vals.append(QString::number(ds.origin[0]) + ", " + QString::number(ds.origin[1]));
            vals.append(QString::number(ds.pixel_size[0]) + ", " + QString::number(ds.pixel_size[1]));
            emit this->metadata(vals);
        };
        auto indices = [this](QStringList indices) {
            for (QString &index : indices) {
                index = index.toLower();
                if (!(index == "ndwi" || index == "andwi" || index == "wi2015"))
                    // if (index != "cdom_ndwi")
                    continue;
                QMap<QString, QString> options = {{"preview_type", get_type_by_index(index)}, {"scalebar", "1"}, {"mask", "0"}};
                send_request("command", proto.calc_index(index), options);
            }
            change_page(PAGE::RESULT);
        };

        disconnect(self.import_p, nullptr, nullptr, nullptr);
        disconnect(self.result_p, nullptr, nullptr, nullptr);
        disconnect(this, &MainWindow::to_satellite_select_page, nullptr, nullptr);
        connect(self.process_p, &ProcessPage::preview, preview);
        connect(self.process_p, &ProcessPage::require_metadata, metadata);
        connect(this, &MainWindow::metadata, self.process_p, &ProcessPage::fill_metadata);
        connect(self.process_p, &ProcessPage::indices, indices);

        self.page = PAGE::SELECTION;

        if (self.proc_level == PROC_LEVEL::LANDSAT_L2SP) {
            self.process_p->show_temperature_toa(false);
        } else if (self.proc_level == PROC_LEVEL::LANDSAT_L1TP) {
            self.process_p->show_temperature_toa(true);
        }
        ui->pb_back->show();
        ui->widget_main->layout()->addWidget(self.process_p);
        self.process_p->show();
        break;
    }
    case PAGE::RESULT: {
        auto preview = [this](QString mask) {
            uint                   width = self.result_p->get_preview_width();
            uint                   height = self.result_p->get_preview_height();
            QMap<QString, QString> options = {{"preview_type", "summary"}, {"scalebar", "0"}, {"mask", mask}};
            send_request("command", proto.calc_preview("nat_col", width, height), options);
        };
        auto refresh_previews = [this, preview]() {
            uint width = self.result_p->get_preview_width();
            uint height = self.result_p->get_preview_height();
            for (DATASET &ds : self.datasets) {
                if (!ds.index.isEmpty()) {
                    QMap<QString, QString> options = {{"preview_type", get_type_by_index(ds.index)}, {"scalebar", "1"}, {"mask", "0"}};
                    send_request("command", proto.calc_preview(ds.index, width, height), options);
                }
            }
            send_request("command", proto.generate_description("summary", "ru"));
            preview("1");
        };
        auto export_index = [this](QString type) {
            QString index = get_index_by_type(type);
            for (DATASET &ds : self.datasets) {
                if (ds.index == index) {
                    QJsonObject data = {{"result", QJsonObject{{"url", ds.url}}}};
                    send_request("resource", data);
                    return;
                }
            }
        };

        disconnect(self.import_p, nullptr, nullptr, nullptr);
        disconnect(self.process_p, nullptr, nullptr, nullptr);
        connect(self.result_p, &ResultPage::update_all_previews, refresh_previews);
        connect(self.result_p, &ResultPage::export_index, export_index);
        connect(self.result_p, &ResultPage::export_text, [](QString t) { qDebug() << t; });

        self.page = PAGE::RESULT;

        ui->pb_back->show();
        ui->widget_main->layout()->addWidget(self.result_p);
        self.result_p->show();
        preview("0");
        break;
    }
    default:
        return;
    }
}

void MainWindow::lock_interface() {
    if (self.req_ids.length() == 0) {
        self.import_p->setEnabled(true);
        self.process_p->setEnabled(true);
        self.result_p->setEnabled(true);
    } else {
        self.import_p->setEnabled(false);
        self.process_p->setEnabled(false);
        self.result_p->setEnabled(false);
    }
}

void MainWindow::on_pb_back_clicked() {
    switch (self.page) {
    case PAGE::IMPORT:
        return;
    case PAGE::IMPORT_CUSTOM_BANDS:
        emit to_satellite_select_page();
        break;
    case PAGE::SELECTION:
        send_request("command", proto.end_session());
        change_page(PAGE::IMPORT);
        break;
    case PAGE::RESULT:
        change_page(PAGE::SELECTION);
        break;
    default:
        return;
    }
}

void MainWindow::on_pb_show_log_clicked() {
    if (ui->plainTextEdit_log->isVisible()) {
        ui->plainTextEdit_log->hide();
        ui->pb_show_log->setText("▴");
    } else {
        ui->plainTextEdit_log->show();
        ui->pb_show_log->setText("▾");
    }
}

void MainWindow::closeEvent(QCloseEvent *e) {
    if (self.page != PAGE::IMPORT) {
        QMessageBox *msg = new QMessageBox(this);
        QPushButton *n = new QPushButton("Нет");
        msg->setWindowTitle("Вы уверены?");
        msg->setText("Выйти из программы?");
        msg->addButton("Да", QMessageBox::YesRole);
        msg->addButton(n, QMessageBox::NoRole);
        msg->setDefaultButton(n);
        msg->exec();
        if (msg->clickedButton() == n) {
            e->ignore();
        } else {
            send_request("command", proto.end_session());
            // send_request -> finish server
            e->accept();
        }
        n->deleteLater();
        msg->deleteLater();
    } else {
        send_request("command", proto.end_session());
        // send_request -> finish server
    }
}
