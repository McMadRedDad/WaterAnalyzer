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
}

MainWindow::~MainWindow() {
    delete ui;
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

void MainWindow::import_clicked() {
    // while (item) => hide()
    state.pages[0]->hide();
    ui->widget_main->layout()->removeWidget(state.pages[0]);
    ui->widget_main->layout()->addWidget(state.pages[1]);
    state.pages[1]->show();
    disconnect(state.pages[0], &ClickableQWidget::clicked, this, &MainWindow::import_clicked);

    state.page = STATE::CurrPage::SELECTION;
}
