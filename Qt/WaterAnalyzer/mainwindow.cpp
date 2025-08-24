#include "mainwindow.hpp"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), ui(new Ui::MainWindow) {
  ui->setupUi(this);

  self.import_p = new ImportPage();
  //
  //
  change_page(PAGE::IMPORT);

  backend_ip = QHostAddress::LocalHost;
  backend_port = 42069;
  net_man = new QNetworkAccessManager(this);
  // connect(net_man, &QNetworkAccessManager::finished, this,
  //         &MainWindow::handle_response);
  proto = JsonProtocol("1.0.0");

  connect(&timer_status, &QTimer::timeout,
          [this]() { ui->lbl_status->clear(); });
}

MainWindow::~MainWindow() {
  delete ui;

  if (self.import_p) {
    delete self.import_p;
    self.import_p = nullptr;
  }
  // if (self.import_p) {
  //     delete self.import_p;
  //     self.import_p = nullptr;
  // }
  // if (self.import_p) {
  //     delete self.import_p;
  //     self.import_p = nullptr;
  // }

  if (net_man) {
    delete net_man;
    net_man = nullptr;
  }
}

void MainWindow::send_request(QString type, QJsonObject data) {
  if (backend_ip.isNull()) {
    return;
  }

  if (type == "command") {
    QNetworkRequest req("http://" + backend_ip.toString() + ":" +
                        QString::number(backend_port) + "/api/" +
                        data["operation"].toString());
    req.setHeader(QNetworkRequest::ContentTypeHeader,
                  "application/json; charset=utf-8");
    req.setRawHeader("Accept", "application/json; charset=utf-8");
    req.setRawHeader("Protocol-Version", proto.get_proto_version().toUtf8());
    req.setRawHeader("Request-ID",
                     QString::number(data["id"].toInt()).toUtf8());
    QNetworkReply *response = net_man->post(req, QJsonDocument(data).toJson());
    connect(response, &QNetworkReply::finished, this,
            [this, response] { handle_response(response); });
    connect(response, &QNetworkReply::errorOccurred, [this, response] {
      append_log("bad", "error");
      response->deleteLater();
    });
    // net_man->post(req, QJsonDocument(data).toJson());
  } else if (type == "resource") {
    QJsonObject result = data["result"].toObject();
    QNetworkRequest req("http://" + backend_ip.toString() + ":" +
                        QString::number(backend_port) +
                        result["url"].toString());
    req.setRawHeader("Accept", "image/png");
    req.setRawHeader("Protocol-Version", proto.get_proto_version().toUtf8());
    req.setRawHeader("Request-ID",
                     QString::number(proto.get_counter()).toUtf8());
    proto.inc_counter();
    req.setRawHeader("Width",
                     QString::number(result["width"].toInt()).toUtf8());
    req.setRawHeader("Height",
                     QString::number(result["height"].toInt()).toUtf8());
    QNetworkReply *response = net_man->get(req);
    connect(response, &QNetworkReply::finished, this,
            [this, response] { handle_response(response); });
    connect(response, &QNetworkReply::errorOccurred, [this, response] {
      append_log("bad", "error");
      response->deleteLater();
    });
    // net_man->get(req);
  } else {
    append_log("bad", QString("Неподдерживаемый тип запроса передан в "
                              "функцию 'send_request': %1.")
                          .arg(type));
    set_status_message(false, "Неподдерживаемый тип запроса");
  }
}

void MainWindow::handle_response(QNetworkReply *response) {
  if (response->error() != QNetworkReply::NoError) {
    if (!response->attribute(QNetworkRequest::HttpStatusCodeAttribute)
             .isValid()) {
      append_log("bad", "Ошибка соединения с сервером: " +
                            response->errorString() + ".");
      set_status_message(false, "Ошибка соединения с сервером");
      response->deleteLater();
      return;
    }

    QList<QNetworkReply::RawHeaderPair> raw_headers =
        response->rawHeaderPairs();
    for (QNetworkReply::RawHeaderPair header : raw_headers) {
      if (QString::fromUtf8(header.first).toLower() == "reason") {
        append_log(
            "bad",
            QString("Некорректный HTTP-запрос к серверу: %1 %2, Reason: %3.")
                .arg(response
                         ->attribute(QNetworkRequest::HttpStatusCodeAttribute)
                         .toString(),
                     response
                         ->attribute(QNetworkRequest::HttpReasonPhraseAttribute)
                         .toString(),
                     QString::fromUtf8(header.second)));
        set_status_message(false, "Некорректный HTTP-запрос");
        response->deleteLater();
        return;
      }
    }

    QJsonObject json = QJsonDocument::fromJson(response->readAll()).object();
    append_log("bad", "Некорректный JSON-запрос к серверу: " +
                          QString::number(json["status"].toInt()) + " " +
                          json["result"].toObject()["error"].toString() + ".");
    set_status_message(false, "Некорректный JSON-запрос");
    response->deleteLater();
    return;
  }

  if (response->operation() == QNetworkAccessManager::GetOperation) {
    process_get(response->request().url(), response->readAll());
  } else if (response->operation() == QNetworkAccessManager::PostOperation) {
    process_post(response->request().url(), response->readAll());
  } else {
    append_log("bad", "Неподдерживаемый тип запроса к серверу.");
    set_status_message(false, "Неподдерживаемый тип запроса");
  }
  response->deleteLater();
}

void MainWindow::process_get(QUrl endpoint, QByteArray body) {
  QString type = endpoint.toString().split("/").last().split("?").first();
  if (type == "preview") {
    QPixmap preview;
    preview.loadFromData(body, "PNG");
    QLabel *l = new QLabel();
    l->setAttribute(Qt::WA_DeleteOnClose);
    l->setPixmap(preview);
    l->show();
  } else if (type == "index") {
    QString path = QFileDialog::getSaveFileName(this, "Сохранить файл GeoTiff",
                                                QDir::homePath());
    if (path.isEmpty()) {
      append_log("bad", "Запись файла отменена.");
      set_status_message(false, "Файл не сохранён");
      return;
    }
    if (!(path.endsWith(".tif") || path.endsWith(".tiff") ||
          path.endsWith(".TIF") || path.endsWith(".TIFF"))) {
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
      append_log("bad", "Не удалось записать файл " + path +
                            " целиком. Скорее всего, файл повреждён.");
      set_status_message(false, "Не удалось записать файл");
    } else {
      append_log("good", "Файл " + path + " успешно сохранён.");
      set_status_message(true, "Файл успешно сохранён");
    }
  } else {
    append_log("info",
               "Запрошена неизвестный тип ресурса, но сервер его обработал: " +
                   type + ".");
    set_status_message(false, "Неизвестный тип ресурса");
  }
}

void MainWindow::process_post(QUrl endpoint, QByteArray body) {
  QString command = endpoint.toString().split("/").last();
  QJsonObject result =
      QJsonDocument::fromJson(body).object()["result"].toObject();

  if (command == "PING") {
    append_log("good", "Ответ сервера: " + result["data"].toString() + ".");
    set_status_message(true, result["data"].toString());
  } else if (command == "SHUTDOWN") {
    append_log("good", "Сервер завершил работу.");
    set_status_message(true, "Сервер завершил работу");
  } else if (command == "import_gtiff") {
    QJsonObject info = result["info"].toObject();
    self.file_ids[result["file"].toString()] = result["id"].toInt();
    append_log("info", "Id: " + QString::number(result["id"].toInt()) +
                           ", file: " + result["file"].toString() + ".");
    set_status_message(true, "Изображение успешно загружено");
  } else if (command == "calc_preview") {
    append_log("info", result["url"].toString() + ", " +
                           QString::number(result["width"].toInt()) + "x" +
                           QString::number(result["height"].toInt()));
    set_status_message(true, "Превью успешно создано");
    send_request("resource", QJsonDocument::fromJson(body).object());
  } else if (command == "calc_index") {
    append_log("info", result["url"].toString() + " -> " +
                           result["info"].toObject()["projection"].toString() +
                           ".");
    set_status_message(true, "Индекс успешно рассчитан");

    //

    QNetworkRequest req("http://" + backend_ip.toString() + ":" +
                        QString::number(backend_port) +
                        result["url"].toString());
    req.setRawHeader("Accept", "image/tiff");
    req.setRawHeader("Protocol-Version", proto.get_proto_version().toUtf8());
    req.setRawHeader("Request-ID",
                     QString::number(proto.get_counter()).toUtf8());
    proto.inc_counter();
    QNetworkReply *response = net_man->get(req);
    connect(response, &QNetworkReply::finished,
            [this, response] { handle_response(response); });
    connect(response, &QNetworkReply::errorOccurred,
            [response] { response->deleteLater(); });

    //

  } else {
    append_log("info",
               "Запрошена неизвестная команда, но сервер её обработал: " +
                   command + ".");
    set_status_message(false, "Неизвестная команда");
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
  if (type == "good") {
    html = "<span style=\"color: lightgreen;\">" + line + "</span>";
  } else if (type == "bad") {
    html = "<span style=\"color: tomato;\">" + line + "</span>";
  } else if (type == "info") {
    html = line;
  } else {
    html = line;
  }
  ui->plainTextEdit_log->appendHtml(html);
}

void MainWindow::change_page(PAGE to) {
  QWidget *w = ui->widget_main->layout()->widget();
  if (w) {
    w->hide();
    ui->widget_main->layout()->removeWidget(w);
    w = nullptr;
  }

  switch (to) {
  case PAGE::IMPORT:
    connect(self.import_p, &ImportPage::directory, [this](QDir dir) {
      int counter = 0;
      for (QString f : dir.entryList()) {
        if (f.endsWith(".tif") || f.endsWith(".tiff") || f.endsWith(".TIF") ||
            f.endsWith(".TIFF")) {
          send_request("command",
                       proto.import_gtiff(dir.absolutePath() + "/" + f));
          counter++;
        }
      }
      if (counter == 0) {
        append_log("bad",
                   QString("В выбранной директории %1 нет снимков GeoTiff.")
                       .arg(dir.absolutePath()));
        set_status_message(false, "В выбранной директории нет снимков");
        return;
      }
      self.dir = dir;
    });
    self.page = PAGE::IMPORT;
    self.dir = QDir();
    // self.file_ids.clear();
    ui->pb_back->hide();
    ui->widget_main->layout()->addWidget(self.import_p);
    self.import_p->show();
    break;
  case PAGE::SELECTION:
    // ui->widget_main->layout()->addWidget(state.pages[1]);
    // state.pages[1]->show();
    self.page = PAGE::SELECTION;
    break;
  case PAGE::RESULT:
    //
    break;
  default:
    return;
  }
}

void MainWindow::on_pb_back_clicked() {
  switch (self.page) {
  case PAGE::IMPORT: {
    send_request("command", proto.shutdown());
    self.page = PAGE::BAD;
    break;
  }
  case PAGE::SELECTION: {
    change_page(PAGE::IMPORT);
    // connect(state.pages[0], &ClickableQWidget::clicked, this,
    //         &MainWindow::import_clicked);

    // int ids[3] = {-1, -1, -1};
    // for (QString f : state.selected_dir.entryList()) {
    //   if (f.endsWith("_B4.TIF")) {
    //     ids[0] =
    //     state.file_ids.value(state.selected_dir.absoluteFilePath(f));
    //   }
    //   if (f.endsWith("_B3.TIF")) {
    //     ids[1] =
    //     state.file_ids.value(state.selected_dir.absoluteFilePath(f));
    //   }
    //   if (f.endsWith("_B2.TIF")) {
    //     ids[2] =
    //     state.file_ids.value(state.selected_dir.absoluteFilePath(f));
    //   }
    // }
    // send_request("command", proto.calc_preview(ids[0], ids[1], ids[2]));

    // QNetworkRequest req("http://" + backend_ip.toString() + ":" +
    //                     QString::number(backend_port) +
    //                     QString("/resource/index?id=0"));
    // req.setRawHeader("Accept", "image/tiff");
    // req.setRawHeader("Protocol-Version", proto.get_proto_version().toUtf8());
    // req.setRawHeader("Request-ID",
    //                  QString::number(proto.get_counter()).toUtf8());
    // proto.inc_counter();
    // net_man->get(req);

    send_request(
        "command",
        proto.import_gtiff("/home/tim/Учёба/Test "
                           "data/LC09_L1TP_188012_20230710_20230710_02_T1/"
                           "LC09_L1TP_188012_20230710_20230710_02_T1_B5.TIF"));
    send_request("command", proto.calc_preview(0, 0, 0));
    send_request("command", proto.calc_index("test", QList<uint>{0, 0}));

    self.dir = QDir();
    self.file_ids.clear();
    break;
  }
  case PAGE::RESULT: {
    //
    break;
  }
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

void MainWindow::import_clicked() {
  // QDir dir = QFileDialog::getExistingDirectory(this, "Открыть директорию",
  //                                              QDir::homePath());
  // int counter = 0;
  // for (QString f : dir.entryList()) {
  //   if (f.endsWith(".tif") || f.endsWith(".tiff") || f.endsWith(".TIF") ||
  //       f.endsWith(".TIFF")) {
  //     // send_request("command", proto.import_gtiff(dir.absolutePath() + "/"
  //     + f)); counter++;
  //   }
  // }
  // if (counter == 0) {
  //   append_log("bad", QString("В выбранной директории %1 нет снимков
  //   GeoTiff.")
  //                         .arg(dir.absolutePath()));
  //   set_status_message(false, "В выбранной директории нет снимков");
  //   return;
  // }
  // state.selected_dir = dir;

  // send_request(
  //     "command",
  //     proto.import_gtiff("/home/tim/Учёба/Test "
  //                        "data/LC09_L1TP_188012_20230710_20230710_02_T1/"
  //                        "LC09_L1TP_188012_20230710_20230710_02_T1_B2.TIF"));
  // send_request(
  //     "command",
  //     proto.import_gtiff("/home/tim/Учёба/Test "
  //                        "data/LC09_L1TP_188012_20230710_20230710_02_T1/"
  //                        "LC09_L1TP_188012_20230710_20230710_02_T1_B3.TIF"));
  // send_request(
  //     "command",
  //     proto.import_gtiff("/home/tim/Учёба/Test "
  //                        "data/LC09_L1TP_188012_20230710_20230710_02_T1/"
  //                        "LC09_L1TP_188012_20230710_20230710_02_T1_B4.TIF"));
  // // send_request("command", proto.import_gtiff(
  // //                             "/home/tim/Учёба/Test
  // //                             data/dacha_dist_10px.tif"));

  change_page(PAGE::SELECTION);
  // disconnect(state.pages[0], &ClickableQWidget::clicked, this,
  //            &MainWindow::import_clicked);
}
