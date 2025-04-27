#include "mainwindow.hpp"
#include "ui_mainwindow.h"
#include "uibuilder.hpp"

MainWindow::MainWindow(QWidget* parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow) {
    ui->setupUi(this);

    state.pages.append(UiBuilder::build_import_page(ui->widget_main));
    state.pages.append(UiBuilder::build_selection_page(ui->widget_main));
    state.pages.append(UiBuilder::build_results_page(ui->widget_main));
    foreach (QWidget* w, state.pages) {
        w->hide();
    }

    ui->widget_main->layout()->addWidget(state.pages[0]);
    state.pages[0]->show();
    connect(state.pages[0], &ClickableQWidget::clicked, this, &MainWindow::import_clicked);

    connect(&timer_status, &QTimer::timeout, this, &MainWindow::clear_status);

    state.page = STATE::CurrPage::IMPORT;

    backend = nullptr;
    json_sock = nullptr;
    http_sock = nullptr;

    prepare_backend();
    QStringList args;
    args << "-u" // "-u" for unbuffered stdout
         << "/home/tim/Учёба/5 семестр/Дешифрирование аэкрокосмических снимков/Курсовая/code/python/server.py";
    backend->start("python", args);
}

MainWindow::~MainWindow() {
    delete ui;

    if (json_sock) {
        delete json_sock;
        json_sock = nullptr;
    }
    if (http_sock) {
        delete http_sock;
        http_sock = nullptr;
    }
    if (backend) {
        delete backend;
        backend = nullptr;
    }
}

void MainWindow::set_status_message(bool good, QString message, short msec) {
    if (timer_status.isActive()) {
        timer_status.stop();
    }

    if (good) {
        ui->label_status->setStyleSheet("color: lightgreen;");
    } else {
        ui->label_status->setStyleSheet("color: lightred;");
    }
    ui->label_status->setText(message);

    timer_status.start(msec);
}

void MainWindow::clear_status() {
    ui->label_status->clear();
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

void MainWindow::prepare_backend() {
    if (!backend) {
        backend = new QProcess(this);
    }
    if (!json_sock) {
        json_sock = new QTcpSocket(this);
    }
    if (!http_sock) {
        http_sock = new QTcpSocket(this);
    }

    backend_host = QHostAddress::LocalHost;
    json_port = 42069;
    http_port = 42070;
    proto = JsonProtocol(json_sock, "1.0.0");

    connect(backend, &QProcess::started, this, [=] { append_log("info", "Процесс бэкенда запущен"); });
    connect(backend, &QProcess::finished, this, [=] { append_log("info", "Процесс бэкенда остановлен"); });
    connect(backend, &QProcess::errorOccurred, this, [=] {
        append_log("bad", QString("Ошибка запуска бэкенда - %1").arg(backend->errorString()));
    });
    connect(backend, &QProcess::readyReadStandardError, this, [=] {
        append_log("bad", QString("Ошибка на бэкенде: %1").arg(backend->readAllStandardError()));
    });
    connect(backend, &QProcess::readyReadStandardOutput, this, &MainWindow::backend_stdout);
}

void MainWindow::backend_stdout() {
    QString stdout = QString(backend->readAllStandardOutput());
    append_log("info", stdout);

    if (stdout.contains("Backend listening on")) {
        init_connections();
    }
}

void MainWindow::init_connections() {
    _connect_socket(json_sock, backend_host, json_port);
    // _connect_socket(http_sock, backend_host, http_port);
}

void MainWindow::_connect_socket(QAbstractSocket* socket, QHostAddress address, quint16 port) {
    if (!socket) {
        return;
    }
    if (socket->state() != QAbstractSocket::UnconnectedState) {
        return;
    }

    socket->connectToHost(address, port);
    connect(socket, &QAbstractSocket::connected, this, [=] {
        QAbstractSocket* sock = qobject_cast<QAbstractSocket*>(sender());
        append_log("good",
                   QString("Успешное подключение к %1 по порту %2").arg(sock->peerAddress().toString(), QString::number(sock->peerPort())));
        sock = nullptr;
    });
    connect(socket, &QAbstractSocket::errorOccurred, this, &MainWindow::socket_error);
    connect(socket, &QAbstractSocket::disconnected, this, [=] {
        QAbstractSocket* sock = qobject_cast<QAbstractSocket*>(sender());
        append_log("info", QString("Подключение к %1:%2 закрыто").arg(sock->peerAddress().toString(), QString::number(sock->peerPort())));
        sock = nullptr;
    });
}

void MainWindow::socket_error() {
    QAbstractSocket* sock = qobject_cast<QAbstractSocket*>(sender());
    switch (sock->error()) {
    case QAbstractSocket::ConnectionRefusedError: {
        append_log("bad", "Критическая ошибка! Не удалось подключиться к бэкенду, пожалуйста, перезапустите программу.");
        break;
    }
    case QAbstractSocket::RemoteHostClosedError: {
        append_log("info", QString("Бэкенд разорвал соединение: %1").arg(sock->errorString()));
        break;
    }
    default:
        append_log("bad",
                   QString("Ошибка на %1:%2 - %3")
                       .arg(sock->peerAddress().toString(), QString::number(sock->peerPort()), sock->errorString()));
        break;
    }
    sock = nullptr;
}

void MainWindow::process_response() {
    json_sock->waitForReadyRead();
    QJsonObject response = QJsonObject();
    response = proto.receive_message();
    qDebug() << response.keys();
    foreach (QString key, response.keys()) {
        qDebug() << QString(key + ": ") << response.value(key);
    }
}

void MainWindow::on_pushButton_back_clicked() {
    switch (state.page) {
    case STATE::CurrPage::BAD: {
        return;
    }
    case STATE::CurrPage::IMPORT: {
        //
        //
        //
        //
        proto.send_message("SHUTDOWN", QJsonObject());
        process_response();
        break;
    }
    case STATE::CurrPage::SELECTION: {
        // proto.send()
        //
        //
        //

        state.pages[1]->hide();
        ui->widget_main->layout()->removeWidget(state.pages[1]);
        ui->widget_main->layout()->addWidget(state.pages[0]);
        state.pages[0]->show();
        connect(state.pages[0], &ClickableQWidget::clicked, this, &MainWindow::import_clicked);

        state.page = STATE::CurrPage::IMPORT;
        break;
    }
    case STATE::CurrPage::RESULT: {
        //
        //
        //
        //

        break;
    }
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

void MainWindow::closeEvent(QCloseEvent* e) {
    if (backend->state() == QProcess::Running) {
        append_log("info", "Бэкенд ещё работет, завершить программу сейчас невозможно");
        e->ignore();
    }
}

void MainWindow::import_clicked() {
    //
    //
    //
    //
    proto.send_message("PING", QJsonObject());
    process_response();

    proto.send_message("PING", QJsonObject());
    process_response();

    proto.send_message("SHUTDOWN", QJsonObject{{"arg1", "val1"}});
    process_response();

    state.pages[0]->hide();
    ui->widget_main->layout()->removeWidget(state.pages[0]);
    ui->widget_main->layout()->addWidget(state.pages[1]);
    state.pages[1]->show();
    disconnect(state.pages[0], &ClickableQWidget::clicked, this, &MainWindow::import_clicked);

    state.page = STATE::CurrPage::SELECTION;
}
