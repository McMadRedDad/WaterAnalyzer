#include "processpage.hpp"
#include "ui_processpage.h"
#include <QHeaderView>

ProcessPage::ProcessPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ProcessPage) {
    ui->setupUi(this);
    tb = new QTableWidget(9, 2);
    tb->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    tb->verticalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    QStringList names = {"Спутник",
                         "Открыто файлов",
                         "Каналы",
                         "Ширина",
                         "Высота",
                         "Проекция",
                         "Единицы измерения",
                         "Координаты привязки",
                         "Размер пикселя"};
    for (int i = 0; i < names.length(); i++) {
        QTableWidgetItem *it = new QTableWidgetItem(names[i]);
        tb->setItem(i, 0, it);
    }
}

ProcessPage::~ProcessPage() {
    delete ui;
    delete tb;
}

void ProcessPage::set_preview(QPixmap image) {
    ui->lbl_preview->clear();
    ui->lbl_preview->setPixmap(image);
}

void ProcessPage::clear_preview() {
    ui->lbl_preview->clear();
}

void ProcessPage::fill_metadata(QStringList metadata) {
    for (int i = 0; i < tb->rowCount() && i < metadata.length(); i++) {
        QTableWidgetItem *prev = tb->takeItem(i, 1);
        delete prev;
        QTableWidgetItem *it = new QTableWidgetItem(metadata[i]);
        tb->setItem(i, 1, it);
    }
    tb->show();
}

void ProcessPage::hide_temperature_toa() {
    ui->combo_temp->removeItem(0);
}

void ProcessPage::on_pb_refresh_clicked() {
    clear_preview();
    emit preview(ui->lbl_preview->width() - 2, ui->lbl_preview->height() - 2);
}

void ProcessPage::on_pb_meta_clicked() {
    emit require_metadata();
}

void ProcessPage::on_pb_go_clicked() {
    QStringList indices;
    indices.append(ui->combo_water->currentText());
    indices.append(ui->combo_tss->currentText());
    indices.append(ui->combo_chloro->currentText());
    indices.append(ui->combo_cdom->currentText());
    if (ui->combo_temp->currentText().contains("Земли")) {
        indices.append("temperature_landsat_lst");
    } else {
        indices.append("temperature_landsat_toa");
    }
    emit this->indices(indices);
}
