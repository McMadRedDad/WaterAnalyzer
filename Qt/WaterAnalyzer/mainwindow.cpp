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
    // ui->plainTextEdit_log->hide();

    connect(&timer_status, &QTimer::timeout, this, &MainWindow::clear_status);

    state.page = STATE::CurrPage::IMPORT;

    prepare_backend();
    QStringList args;
    // args << QString(QCoreApplication::applicationDirPath() + "...");
    args << "-u" // "-u" for unbuffered stdout
         << "/home/tim/Учёба/5 семестр/Дешифрирование аэкрокосмических снимков/Курсовая/code/python/gdal_backend.py";
    backend->start("python", args);
    // init_connections();
}

MainWindow::~MainWindow() {
    delete ui;

    if (backend) {
        backend->waitForFinished();
        delete backend;
        backend = nullptr;
    }
    if (json_sock) {
        json_sock->disconnectFromHost();
        delete json_sock;
        json_sock = nullptr;
    }
    if (http_sock) {
        http_sock->disconnectFromHost();
        delete http_sock;
        http_sock = nullptr;
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

void MainWindow::append_log(QString line) {
    ui->plainTextEdit_log->appendHtml(line);
}

void MainWindow::prepare_backend() {
    backend = new QProcess(this);
    json_sock = new QTcpSocket(this);
    http_sock = new QTcpSocket(this);

    backend_host = QHostAddress::LocalHost;
    json_port = 42069;
    http_port = 42070;

    connect(backend, &QProcess::started, this, [=] { append_log("<span style=\"color: lightgreen;\">Процесс бэкенда запущен</span>"); });
    connect(backend, &QProcess::finished, this, [=] { append_log("Процесс бэкенда остановлен"); });
    connect(backend, &QProcess::errorOccurred, this, [=] {
        append_log(QString("<span style=\"color: tomato;\">Ошибка запуска бэкенда - %1</span>").arg(backend->errorString()));
        // QMessageBox::critical(this, "Критическая ошибка", "Не удалось запустить бэкенд, пожалуйста, перезапустите программу.");
        // close();
    });
    connect(backend, &QProcess::readyReadStandardError, this, [=] {
        append_log(QString("<span style=\"color: tomato;\">Ошибка на бэкенде: %1</span>").arg(backend->readAllStandardError()));
    });
    connect(backend, &QProcess::readyReadStandardOutput, this, &MainWindow::backend_stdout);
}

void MainWindow::backend_stdout() {
    QString stdout = QString(backend->readAllStandardOutput());
    append_log(stdout);

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
        append_log(QString("<span style=\"color: lightgreen;\">Успешное подключение к %1 по порту %2</span>")
                       .arg(sock->peerAddress().toString(), QString::number(sock->peerPort())));
    });
    connect(socket, &QAbstractSocket::errorOccurred, this, &MainWindow::socket_error);
    connect(socket, &QAbstractSocket::readyRead, this, &MainWindow::socket_read);
}

void MainWindow::socket_error() {
    QAbstractSocket* sock = qobject_cast<QAbstractSocket*>(sender());
    append_log(QString("<span style=\"color: tomato;\">Ошибка на %1:%2 - %3</span>")
                   .arg(sock->peerAddress().toString(), QString::number(sock->peerPort()), sock->errorString()));

    switch (sock->error()) {
    case QAbstractSocket::ConnectionRefusedError: {
        QMessageBox::critical(this, "Критическая ошибка", "Не удалось подключиться к бэкенду, пожалуйста, перезапустите программу.");
        // close();
        break;
    }
    default:
        break;
    }
}

void MainWindow::socket_read() {
    QAbstractSocket* sock = qobject_cast<QAbstractSocket*>(sender());
    while (sock->bytesAvailable() > 0) {
        // QByteArray ba = sock->readAll();
        // append_log(QString("Recieved: " + ba));
    }
}

void MainWindow::on_pushButton_back_clicked() {
    switch (state.page) {
    case STATE::CurrPage::BAD: {
        return;
    }
    case STATE::CurrPage::IMPORT: {
        //
        break;
    }
    case STATE::CurrPage::SELECTION: {
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

void MainWindow::closeEvent(QCloseEvent*) {
    json_sock->disconnectFromHost();
    // http_sock->disconnectFromHost();
    // backend.send_shutdown
    backend->waitForFinished();
    delete backend;
    backend = nullptr;
}

void MainWindow::import_clicked() {
    state.pages[0]->hide();
    ui->widget_main->layout()->removeWidget(state.pages[0]);
    ui->widget_main->layout()->addWidget(state.pages[1]);
    state.pages[1]->show();
    disconnect(state.pages[0], &ClickableQWidget::clicked, this, &MainWindow::import_clicked);

    state.page = STATE::CurrPage::SELECTION;

    // QByteArray ba("sdfsdfsdfs");
    // json_sock->write(ba);
    // append_log(QString("Sent: " + ba));
}
