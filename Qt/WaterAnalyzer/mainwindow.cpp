#include "mainwindow.hpp"
#include "ui_mainwindow.h"
#include "uibuilder.hpp"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), ui(new Ui::MainWindow) {
  ui->setupUi(this);

  state.pages.append(UiBuilder::build_import_page(ui->widget_main));
  state.pages.append(UiBuilder::build_selection_page(ui->widget_main));
  state.pages.append(UiBuilder::build_results_page(ui->widget_main));
  for (QWidget *w : state.pages) {
    w->hide();
  }
  ui->widget_main->layout()->addWidget(state.pages[0]);
  state.pages[0]->show();
  connect(state.pages[0], &ClickableQWidget::clicked, this,
          &MainWindow::import_clicked);
  state.page = STATE::Page::IMPORT;

  backend_ip = QHostAddress::LocalHost;
  backend_port = 42069;
  net_man = new QNetworkAccessManager(this);
  connect(net_man, &QNetworkAccessManager::finished, this,
          &MainWindow::handle_response);
  proto = JsonProtocol("1.0.0");

  connect(&timer_status, &QTimer::timeout, this,
          [this]() { ui->label_status->clear(); });
}

MainWindow::~MainWindow() {
  delete ui;

  if (net_man) {
    delete net_man;
    net_man = nullptr;
  }
}

void MainWindow::send_request(QString type, QString endpoint,
                              QJsonObject data) {
  if (backend_ip.isNull()) {
    return;
  }

  if (type == "command") {
    QNetworkRequest req("http://" + backend_ip.toString() + ":" +
                        QString::number(backend_port) + endpoint);
    req.setHeader(QNetworkRequest::ContentTypeHeader,
                  "application/json; charset=utf-8");
    req.setRawHeader("Accept", "application/json; charset=utf-8");
    req.setRawHeader("Protocol-Version", proto.get_proto_version().toUtf8());
    req.setRawHeader("Request-ID",
                     QString::number(data["id"].toInt()).toUtf8());
    net_man->post(req, QJsonDocument(data).toJson());
  } else if (type == "resource") {
    //
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
    process_get(response->readAll());
  } else if (response->operation() == QNetworkAccessManager::PostOperation) {
    process_post(response->request().url(), response->readAll());
  } else {
    append_log("bad", "Неподдерживаемый тип запроса к серверу.");
    set_status_message(false, "Неподдерживаемый тип запроса");
  }
  response->deleteLater();
}

void MainWindow::process_get(QByteArray body) {}

void MainWindow::process_post(QUrl endpoint, QByteArray body) {
  QString command = endpoint.toString().split("/").last();
  QJsonObject json = QJsonDocument::fromJson(body).object();

  if (command == "PING") {
    append_log("good", "Ответ сервера: " +
                           json["result"].toObject()["data"].toString() + ".");
    set_status_message(true, json["result"].toObject()["data"].toString());
  } else if (command == "SHUTDOWN") {
    append_log("good", "Сервер завершил работу.");
    set_status_message(true, "Сервер завершил работу");
  } else if (command == "import_gtiff") {
    QJsonObject info = json["result"].toObject()["info"].toObject();
    append_log("info", "Id: " + QString::number(
                                    json["result"].toObject()["id"].toInt()));
    set_status_message(true, "Изображение успешно загружено");
  } else {
    append_log("bad",
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
    ui->label_status->setStyleSheet("color: lightgreen;");
  } else {
    ui->label_status->setStyleSheet("color: tomato;");
  }
  ui->label_status->setText(message);

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

void MainWindow::change_page(STATE::Page to) {
  for (QWidget *w : state.pages) {
    w->hide();
    ui->widget_main->layout()->removeWidget(w);
  }
  switch (to) {
  case STATE::Page::IMPORT:
    ui->widget_main->layout()->addWidget(state.pages[0]);
    state.pages[0]->show();
    state.page = STATE::Page::IMPORT;
    break;
  case STATE::Page::SELECTION:
    ui->widget_main->layout()->addWidget(state.pages[1]);
    state.pages[1]->show();
    state.page = STATE::Page::SELECTION;
    break;
  case STATE::Page::RESULT:
    //
    break;
  default:
    return;
  }
}

void MainWindow::on_pushButton_back_clicked() {
  switch (state.page) {
  case STATE::Page::IMPORT:
    send_request("command", "/api/SHUTDOWN", proto.shutdown());
    state.page = STATE::Page::BAD;
    break;
  case STATE::Page::SELECTION:
    change_page(STATE::Page::IMPORT);
    connect(state.pages[0], &ClickableQWidget::clicked, this,
            &MainWindow::import_clicked);
    break;
  case STATE::Page::RESULT:
    //
    break;
  default:
    return;
  }
}

void MainWindow::on_pushButton_showLog_clicked() {
  if (ui->plainTextEdit_log->isVisible()) {
    ui->plainTextEdit_log->hide();
    ui->pushButton_showLog->setText("▾");
  } else {
    ui->plainTextEdit_log->show();
    ui->pushButton_showLog->setText("▴");
  }
}

void MainWindow::closeEvent(QCloseEvent *e) {}

void MainWindow::import_clicked() {
  QDir dir = QFileDialog::getExistingDirectory(this, "Открыть директорию",
                                               QDir::homePath());
  int counter = 0;
  for (QString f : dir.entryList()) {
    if (f.endsWith(".tif") || f.endsWith(".tiff") || f.endsWith(".TIF") ||
        f.endsWith(".TIFF")) {
      send_request("command", "/api/import_gtiff",
                   proto.import_gtiff(dir.absolutePath() + "/" + f));
      counter++;
    }
  }
  if (counter == 0) {
    append_log("bad", QString("В выбранной директории %1 нет снимков GeoTiff.")
                          .arg(dir.absolutePath()));
    set_status_message(false, "В выбранной директории нет снимков");
    return;
  }

  change_page(STATE::Page::SELECTION);
  disconnect(state.pages[0], &ClickableQWidget::clicked, this,
             &MainWindow::import_clicked);
}
