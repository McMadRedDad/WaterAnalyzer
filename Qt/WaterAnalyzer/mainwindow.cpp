#include "mainwindow.hpp"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), ui(new Ui::MainWindow) {
    ui->setupUi(this);

    self.import_p = new ImportPage();
    self.process_p = new ProcessPage();
    self.result_p = new ResultPage();
    change_page(PAGE::IMPORT);
    self.curr_req_id = -1;

    backend_ip = QHostAddress::LocalHost;
    backend_port = 42069;
    net_man = new QNetworkAccessManager(this);
    proto = JsonProtocol("1.0.0");

    connect(&timer_status, &QTimer::timeout, [this]() { ui->lbl_status->clear(); });
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
        self.curr_req_id = data["id"].toInt();
        lock_interface(true);
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
        self.curr_req_id = proto.get_counter();

        QString type = result["url"].toString();
        type = type.split('?').first().split('/').last();
        if (type == "preview") {
            if (!options.contains("scalebar")) {
                return;
            }

            req.setUrl(req.url().toString() + "&sb=" + options.value("scalebar"));
            req.setRawHeader("Accept", "image/png");
            req.setRawHeader("Width", QString::number(result["width"].toInt()).toUtf8());
            req.setRawHeader("Height", QString::number(result["height"].toInt()).toUtf8());
        } else if (type == "index") {
            req.setRawHeader("Accept", "image/tiff");
        } else {
            return;
        }
        proto.inc_counter();

        lock_interface(true);
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
        lock_interface(false);
        return;
    }

    auto raw_header_pairs = response->rawHeaderPairs();
    for (const auto &header : raw_header_pairs) {
        if (QString::fromUtf8(header.first).toLower() == "request-id") {
            if (header.second.toUInt() == self.curr_req_id) {
                lock_interface(false);
                break;
            }
        }
    }
    for (const auto &header : raw_header_pairs) {
        if (QString::fromUtf8(header.first).toLower() == "reason") {
            append_log("bad",
                       QString("Некорректный HTTP-запрос к серверу: %1 %2, Reason: %3.")
                           .arg(response->attribute(QNetworkRequest::HttpStatusCodeAttribute).toString(),
                                response->attribute(QNetworkRequest::HttpReasonPhraseAttribute).toString(),
                                QString::fromUtf8(header.second)));
            set_status_message(false, "Некорректный HTTP-запрос");
            return;
        }
    }

    QJsonDocument jdoc = QJsonDocument::fromJson(response->readAll());
    if (jdoc.isNull()) {
        append_log("bad",
                   QString("Неизвестная ошибка на сервере. Ответ сервера: %1 %2.")
                       .arg(response->attribute(QNetworkRequest::HttpStatusCodeAttribute).toString(),
                            response->attribute(QNetworkRequest::HttpReasonPhraseAttribute).toString()));
        set_status_message(false, "Неизвестная ошибка на сервере");
        lock_interface(false);
        return;
    }

    QJsonObject json = jdoc.object();
    append_log("bad",
               "Некорректный JSON-запрос к серверу: " + QString::number(json["status"].toInt()) + " "
                   + json["result"].toObject()["error"].toString() + ".");
    set_status_message(false, "Некорректный JSON-запрос");
    lock_interface(false);
}

void MainWindow::process_get(QUrl endpoint, QHttpHeaders headers, QByteArray body, QMap<QString, QString> options) {
    if (self.curr_req_id == headers.value("Request-ID").toUInt()) {
        lock_interface(false);
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
            append_log("good", "Файл " + path + " успешно сохранён.");
            set_status_message(true, "Файл успешно сохранён");
        }
    } else {
        append_log("info", "Запрошена неизвестный тип ресурса, но сервер его обработал: " + type + ".");
        set_status_message(false, "Неизвестный тип ресурса");
    }
}

void MainWindow::process_post(QUrl endpoint, QHttpHeaders headers, QByteArray body, QMap<QString, QString> options) {
    if (self.curr_req_id == headers.value("Request-ID").toUInt()) {
        lock_interface(false);
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
        for (auto i = self.files.begin(), end = self.files.end(); i != end; ++i) {
            if (i.value().filename == result["file"].toString()) {
                QJsonObject info = result["info"].toObject();
                i.value().id = result["id"].toInt();
                i.value().width = info["width"].toInt();
                i.value().height = info["height"].toInt();
                i.value().projection = info["projection"].toString();
                i.value().unit = info["unit"].toString();
                i.value().origin[0] = info["origin"].toArray()[0].toDouble();
                i.value().origin[1] = info["origin"].toArray()[1].toDouble();
                i.value().pixel_size[0] = info["pixel_size"].toArray()[0].toDouble();
                i.value().pixel_size[1] = info["pixel_size"].toArray()[1].toDouble();
                break;
            }
        }
        append_log("info", "Файл " + result["file"].toString() + " успешно загружен.");
        set_status_message(true, "Файл успешно загружен");
    } else if (command == "calc_preview") {
        send_request("resource", QJsonDocument::fromJson(body).object(), options);
    } else if (command == "calc_index") {
        DATASET     ds;
        QJsonObject info = result["info"].toObject();
        ds.url = result["url"].toString();
        ds.id = result["url"].toString().split('?').last().split('&').first().split('=').last().toInt();
        ds.width = info["width"].toInt();
        ds.height = info["height"].toInt();
        ds.projection = info["projection"].toString();
        ds.unit = info["unit"].toString();
        ds.origin[0] = info["origin"].toArray()[0].toDouble();
        ds.origin[1] = info["origin"].toArray()[1].toDouble();
        ds.pixel_size[0] = info["pixel_size"].toArray()[0].toDouble();
        ds.pixel_size[1] = info["pixel_size"].toArray()[1].toDouble();
        self.files[result["index"].toString()] = ds;

        uint width = self.result_p->get_preview_width();
        uint height = self.result_p->get_preview_height();
        send_request("command", proto.calc_preview(ds.id, ds.id, ds.id, width, height), options);
        self.result_p->set_caption(get_type_by_index(result["index"].toString()), result["index"].toString().toUpper());

        append_log("info", "Индекс " + result["index"].toString() + " успешно рассчитан.");
        set_status_message(true, "Индекс успешно рассчитан");
    } else {
        append_log("info", "Запрошена неизвестная команда, но сервер её обработал: " + command + ".");
        set_status_message(false, "Неизвестная команда");
    }
}

QString MainWindow::get_type_by_index(QString index) {
    QString indx = index.toLower();
    if (indx == "test" || indx == "wi2015") {
        return "water";
    } else if (indx == "nsmi") {
        return "tss";
    } else {
        return "";
    }
}

QString MainWindow::get_index_by_type(QString type) {
    if (type == "summary") {
        return "";
    } else if (type == "water") {
        for (auto it = self.files.cbegin(), end = self.files.cend(); it != end; ++it) {
            if (it.key() == "test" || it.key() == "wi2015") {
                return it.key();
            }
        }
        return "";
    } else if (type == "tss") {
        for (auto it = self.files.cbegin(), end = self.files.cend(); it != end; ++it) {
            if (it.key() == "nsmi") {
                return it.key();
            }
        }
        return "";
    } else {
        return "";
    }
}

QList<int> MainWindow::select_bands_for_index(QString index) {
    QString indx = index.toLower();
    if (indx == "test") {
        return QList<int>{self.files["L1"].id, self.files["L2"].id};
    } else if (indx == "wi2015") {
        return QList<int>{self.files["L3"].id, self.files["L4"].id, self.files["L5"].id, self.files["L6"].id, self.files["L7"].id};
    } else if (indx == "nsmi") {
        return QList<int>{self.files["L4"].id, self.files["L3"].id, self.files["L2"].id};
    } else {
        return QList<int>{-1};
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
            int counter = 0;
            for (const QString &f : dir.entryList()) {
                if (f.toUpper().endsWith(".TIF") && f.right(7).toUpper().contains('B')) {
                    DATASET ds;
                    ds.filename = dir.absolutePath() + "/" + f;
                    QString band = f.right(8);
                    if (band[0] == '_') {
                        band = band.mid(2, 2).prepend('L');
                    } else {
                        band = band.mid(3, 1).prepend('L');
                    }
                    self.files[band] = ds;
                    send_request("command", proto.import_gtiff(ds.filename));
                    counter++;
                }
            }
            if (counter == 0) {
                append_log("bad", QString("В выбранной директории %1 нет снимков Landsat или Sentinel.").arg(dir.absolutePath()));
                set_status_message(false, "В выбранной директории нет снимков");
                return;
            }
            self.dir = dir;
            change_page(PAGE::SELECTION);
        };
        auto files = [this](QStringList filenames) {
            int counter = 0;
            for (const QString &f : filenames) {
                if (f.toUpper().endsWith(".TIF") && f.right(7).toUpper().contains("B")) {
                    DATASET ds;
                    ds.filename = f;
                    QString band = f.right(8);
                    if (band[0] == '_') {
                        band = band.mid(2, 2).prepend('L');
                    } else {
                        band = band.mid(3, 1).prepend('L');
                    }
                    self.files[band] = ds;
                    send_request("command", proto.import_gtiff(ds.filename));
                    counter++;
                }
            }
            if (counter == 0) {
                append_log("bad", "Не выбрано ни одного снимка Landsat или Sentinel.");
                set_status_message(false, "Не выбрано ни одного снимка");
                return;
            }
            self.dir = filenames[0].section('/', 0, -2);
            change_page(PAGE::SELECTION);
        };
        auto custom_files = [this](QList<QPair<QString, QString>> bands_files) {
            if (bands_files.isEmpty()) {
                append_log("bad", "Не выбрано ни одного файла Tiff.");
                set_status_message(false, "Файлы Tiff не выбраны");
                return;
            }
            for (auto &f : bands_files) {
                DATASET ds;
                ds.filename = f.second;
                self.files[f.first.prepend('L')] = ds;
                send_request("command", proto.import_gtiff(ds.filename));
            }
            self.dir = bands_files[0].second.section('/', 0, -2);
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
        connect(this, &MainWindow::to_satellite_select_page, self.import_p, &ImportPage::to_satellite_select_page);
        connect(self.import_p, &ImportPage::directory, directory);
        connect(self.import_p, &ImportPage::files, files);
        connect(self.import_p, &ImportPage::custom_files, custom_files);

        self.page = PAGE::IMPORT;
        self.dir = QDir();
        self.files.clear();

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
            auto                   it_r = self.files.find("L4");
            auto                   it_g = self.files.find("L3");
            auto                   it_b = self.files.find("L2");
            QMap<QString, QString> options = {{"preview_type", "color"}, {"scalebar", "0"}};
            if (it_r == self.files.end() || it_g == self.files.end() || it_b == self.files.end()) {
                send_request("command", proto.calc_preview(0, 0, 0, width, height), options);
            } else {
                send_request("command", proto.calc_preview(it_r.value().id, it_g.value().id, it_b.value().id, width, height), options);
            }
        };
        auto metadata = [this]() {
            QStringList vals;
            DATASET     ds = self.files.first();
            QStringList keys_l = self.files.keys();
            keys_l.sort();
            QString keys;
            for (QString &k : keys_l) {
                keys.append(k.replace('L', 'B') + ", ");
            }
            keys.chop(2);
            vals.append("Landsat 8/9");
            vals.append(QString::number(self.files.size()));
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
            for (QString index : indices) {
                index = index.toLower();
                QMap<QString, QString> options = {{"preview_type", get_type_by_index(index)}, {"scalebar", "1"}};
                send_request("command", proto.calc_index(index, select_bands_for_index(index)), options);
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

        ui->pb_back->show();
        ui->widget_main->layout()->addWidget(self.process_p);
        self.process_p->show();
        break;
    }
    case PAGE::RESULT: {
        auto preview = [this]() {
            auto                   it_r = self.files.find("L4");
            auto                   it_g = self.files.find("L3");
            auto                   it_b = self.files.find("L2");
            uint                   width = self.result_p->get_preview_width();
            uint                   height = self.result_p->get_preview_height();
            QMap<QString, QString> options = {{"preview_type", "summary"}, {"scalebar", "0"}};
            if (it_r == self.files.end() || it_g == self.files.end() || it_b == self.files.end()) {
                send_request("command", proto.calc_preview(0, 0, 0, width, height), options);
            } else {
                send_request("command", proto.calc_preview(it_r.value().id, it_g.value().id, it_b.value().id, width, height), options);
            }
        };
        auto refresh_previews = [this, preview]() {
            uint width = self.result_p->get_preview_width();
            uint height = self.result_p->get_preview_height();
            for (auto it = self.files.cbegin(), end = self.files.cend(); it != end; ++it) {
                QString key = it.key();
                bool    num;
                key.right(key.size() - 1).toInt(&num);
                if (key[0] == 'L' && num) {
                    continue;
                }

                int                    id = it.value().id;
                QMap<QString, QString> options = {{"preview_type", get_type_by_index(key)}, {"scalebar", "1"}};
                send_request("command", proto.calc_preview(id, id, id, width, height), options);
            }
            preview();
        };
        auto export_index = [this](QString type) {
            QString     index = get_index_by_type(type);
            QJsonObject data = {{"result", QJsonObject{{"url", self.files.value(index).url}}}};
            send_request("resource", data);
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
        preview();
        break;
    }
    default:
        return;
    }
}

void MainWindow::lock_interface(bool on) {
    self.import_p->setEnabled(!on);
    self.process_p->setEnabled(!on);
    self.result_p->setEnabled(!on);
}

void MainWindow::on_pb_back_clicked() {
    switch (self.page) {
    case PAGE::IMPORT:
        return;
    case PAGE::IMPORT_CUSTOM_BANDS:
        emit to_satellite_select_page();
        break;
    case PAGE::SELECTION:
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

void MainWindow::closeEvent(QCloseEvent *e) {}
