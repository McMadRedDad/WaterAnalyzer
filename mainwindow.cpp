#include "mainwindow.hpp"

#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget* parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow) {
    ui->setupUi(this);

    QLabel* t = new QLabel("Нажмите, чтобы открыть папку со снимком");
    t->setAlignment(Qt::AlignCenter);
    QVBoxLayout* l = new QVBoxLayout;
    l->addWidget(t);
    ui->widget_main->setLayout(l);
    // connect(ui->widget_main, &ClickableWidget::clicked, this, &MainWindow::import_clicked);

    ui->plainTextEdit_log->hide();
}

MainWindow::~MainWindow() {
    delete ui;
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

void MainWindow::import_clicked() {
    // disconnect(ui->widget_main, &ClickableWidget::clicked, this, &MainWindow::import_clicked);
    // ui->widget_main->layout
}
